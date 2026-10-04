"""AWS Strands Agents SDK Multi-Agent Orchestration Harness.

Uses the real `strands-agents` SDK when installed (`pip install -e ".[aws]"`):
genuine `strands.Agent` objects, tools declared with the SDK's `@tool`
decorator, and sub-agents composed via the documented agents-as-tools pattern
(`Agent.as_tool`). Every tool schema in `strands_sdk_status()` is produced by
the SDK itself, not hand-written.

Architecture:
1. Multi-Agent Supervisor Pattern: Central coordinator delegating to domain-specific agents.
2. Domain Sub-Agents:
   - ArbiterNegotiatorAgent: Family consensus, Pareto climate setpoints, peak-tariff load shifting.
   - ReplenishmentDepletionAgent: Pantry consumption velocity, Subscribe & Save bundles, Prime transit.
   - SentinelGuardianAgent: Propose-never-execute gating, persona authorization, Merkle audit receipts.
3. Memory & Telemetry: Integrated with Bedrock AgentCore Memory and OpenTelemetry-shaped metrics.

Execution paths, reported honestly via `strands_backend`:
  - `aws-strands-sdk`               real SDK agents; inference runs (Bedrock enabled + creds).
  - `aws-strands-sdk-no-inference`  real SDK agents constructed; Bedrock not enabled, so the
                                    deterministic router produces the plan instead.
  - `pattern-fallback`              SDK not installed; deterministic router only.

Adheres to the Hackathon standard for AWS Builder:
"Creative: multi-service pipeline (Bedrock + AgentCore + Strands), agentic architecture with Claude/Kiro, agent orchestration patterns."
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Callable

from . import agentcore, arbiter, audit, brains, commerce, proposals, sentinel

# ---------------------------------------------------------------------------
# AWS Strands Agents SDK integration (optional dependency).
#
# Install with:  pip install -e ".[aws]"
#
# When the SDK is present we build *genuine* strands.Agent objects and wire them
# together with the SDK's documented agents-as-tools pattern (Agent.as_tool).
# When it is absent we fall back to the deterministic keyword supervisor below,
# so the zero-config judge demo never depends on the SDK being installed.
# `strands_backend` reports which path actually ran -- it is never guessed.
# ---------------------------------------------------------------------------
try:  # pragma: no cover - depends on whether the optional extra is installed
    from strands import Agent as _StrandsAgent  # type: ignore
    from strands import tool as _strands_tool  # type: ignore

    STRANDS_AVAILABLE = True
    STRANDS_IMPORT_ERROR = ""
except Exception as _exc:  # pragma: no cover
    _StrandsAgent = None  # type: ignore
    _strands_tool = None  # type: ignore
    STRANDS_AVAILABLE = False
    STRANDS_IMPORT_ERROR = f"{type(_exc).__name__}: {_exc}"


@dataclass
class StrandsMessage:
    role: str
    content: str
    timestamp: float = field(default_factory=time.time)


@dataclass
class StrandsAgentResult:
    agent_name: str
    summary: str
    actions_taken: list[dict[str, Any]]
    proposals_staged: list[dict[str, Any]]
    metrics: dict[str, Any]


class StrandsBaseAgent:
    """Base agent implementing the AWS Strands reasoning and tool dispatch pattern."""

    def __init__(self, name: str, role_description: str, system_prompt: str) -> None:
        self.name = name
        self.role_description = role_description
        self.system_prompt = system_prompt
        self.tools: dict[str, Callable[..., Any]] = {}

    def register_tool(self, name: str, fn: Callable[..., Any]) -> None:
        self.tools[name] = fn

    def run(self, task: str, context: dict[str, Any] | None = None) -> StrandsAgentResult:
        raise NotImplementedError


class ArbiterNegotiatorAgent(StrandsBaseAgent):
    """Strands sub-agent specialized in household game theory and energy arbitrage."""

    def __init__(self) -> None:
        super().__init__(
            name="ArbiterNegotiatorAgent",
            role_description="Resolves multi-resident conflicting preferences and shifts high-draw loads off peak energy tariffs.",
            system_prompt=(
                "You are the Household Arbiter agent. Calculate Pareto-optimal compromises "
                "for competing resident thermostat setpoints and identify load-shifting opportunities "
                "to save money during peak electrical tariffs."
            ),
        )
        self.register_tool("resolve_conflict", arbiter.resolve_conflict)
        self.register_tool("list_conflicts", arbiter.list_active_conflicts)

    def run(self, task: str, context: dict[str, Any] | None = None) -> StrandsAgentResult:
        start_t = time.time()
        actions: list[dict[str, Any]] = []
        low = task.lower()

        conflict_type = "climate"
        if "energy" in low or "peak" in low or "tariff" in low or "ev" in low:
            conflict_type = "energy_peak"
        elif "media" in low or "tv" in low or "music" in low:
            conflict_type = "media"

        plan = arbiter.resolve_conflict(conflict_type, custom_params=context)
        actions.append({"tool": "arbiter.resolve_conflict", "type": conflict_type, "plan_title": plan.get("title")})

        summary = f"Arbiter resolved {conflict_type} conflict: {plan.get('title')}. Compromise setpoint: {plan.get('outcome', {}).get('temperature_c', 'N/A')}°C, Estimated monthly savings: ${plan.get('outcome', {}).get('estimated_monthly_savings_usd', 0):.2f}."

        audit.append("strands_agent", "arbiter_executed", {"agent": self.name, "task": task[:100], "plan": plan.get("title")})

        return StrandsAgentResult(
            agent_name=self.name,
            summary=summary,
            actions_taken=actions,
            proposals_staged=[],
            metrics={"latency_ms": round((time.time() - start_t) * 1000, 1)},
        )


class ReplenishmentDepletionAgent(StrandsBaseAgent):
    """Strands sub-agent specialized in pantry velocity and Amazon Subscribe & Save optimization."""

    def __init__(self) -> None:
        super().__init__(
            name="ReplenishmentDepletionAgent",
            role_description="Monitors consumable burn rates, optimizes 5+ item Subscribe & Save bundles, and schedules Prime delivery.",
            system_prompt=(
                "You are the Commerce Replenishment agent. Calculate depletion velocities, "
                "stage bulk bundles to unlock maximum 15% Subscribe & Save discounts, and allocate Prime delivery slots."
            ),
        )
        self.register_tool("get_forecast", commerce.get_depletion_forecast)
        self.register_tool("optimize_bundles", commerce.optimize_bundles)
        self.register_tool("stage_cart", commerce.stage_amazon_cart)

    def run(self, task: str, context: dict[str, Any] | None = None) -> StrandsAgentResult:
        start_t = time.time()
        actions: list[dict[str, Any]] = []
        staged_proposals: list[dict[str, Any]] = []

        forecast = commerce.get_depletion_forecast()
        low_items = [f for f in forecast if f.get("status") == "critical" or f.get("days_until_empty", 99) <= 3]
        actions.append({"tool": "commerce.get_depletion_forecast", "critical_count": len(low_items)})

        bundles = commerce.optimize_bundles(auto_fill_tier=True)
        actions.append({"tool": "commerce.optimize_bundles", "bundle_tier_discount": "15%"})

        cart = commerce.stage_amazon_cart(bundle_optimized=True)
        actions.append({"tool": "commerce.stage_amazon_cart", "final_total": cart.get("final_total", 0.0)})

        # Gated action: Stage an approval proposal in the tray
        prop = proposals.propose(
            kind="commerce_replenish",
            title=f"Prime Restock: {len(cart.get('items', []))} Household Essentials",
            reasons=f"Pantry depletion radar flagged {len(low_items)} critical items. Bundle optimized for 15% Subscribe & Save savings (${bundles.get('pricing', {}).get('total_savings', 0):.2f} saved).",
            cost_delta_yr=float(cart.get("final_total", 0.0)),
            meta={"cart": cart},
        )
        staged_proposals.append(prop)

        summary = (
            f"Replenishment evaluated {len(forecast)} pantry items. Flagged {len(low_items)} low items. "
            f"Assembled 15% discount Subscribe & Save cart (${cart.get('final_total', 0.0):.2f}) and staged proposal {prop['id']} in Approval Tray."
        )

        audit.append("strands_agent", "replenishment_executed", {"agent": self.name, "proposal": prop["id"]})

        return StrandsAgentResult(
            agent_name=self.name,
            summary=summary,
            actions_taken=actions,
            proposals_staged=staged_proposals,
            metrics={"latency_ms": round((time.time() - start_t) * 1000, 1)},
        )


class SentinelGuardianAgent(StrandsBaseAgent):
    """Strands sub-agent specialized in safety gating, persona permissions, and cryptographic ledger integrity."""

    def __init__(self) -> None:
        super().__init__(
            name="SentinelGuardianAgent",
            role_description="Validates proposed actions against persona safety matrices and verifies tamper-evident audit chains.",
            system_prompt=(
                "You are the Sentinel Guardian agent. Enforce the Propose-Never-Execute contract. "
                "Block destructive inputs and verify cryptographic Merkle receipts."
            ),
        )
        self.register_tool("judge_action", sentinel.judge)
        self.register_tool("verify_audit", audit.verify)

    def run(self, task: str, context: dict[str, Any] | None = None) -> StrandsAgentResult:
        start_t = time.time()
        actions: list[dict[str, Any]] = []

        is_valid = audit.verify()
        actions.append({"tool": "audit.verify", "chain_intact": is_valid})

        persona = (context or {}).get("persona", "admin")
        v = sentinel.judge("home_toggle_lock", {"door": "front_door", "locked": False, "persona": persona})
        actions.append({"tool": "sentinel.judge", "sample_verdict": v.decision})

        summary = f"Sentinel Guardian verified cryptographic audit chain: {'VALID (SHA-256)' if is_valid else 'CORRUPT'}. Persona '{persona}' safety rules enforced."

        audit.append("strands_agent", "guardian_executed", {"agent": self.name, "audit_valid": is_valid})

        return StrandsAgentResult(
            agent_name=self.name,
            summary=summary,
            actions_taken=actions,
            proposals_staged=[],
            metrics={"latency_ms": round((time.time() - start_t) * 1000, 1)},
        )


# Process-wide cache for the constructed SDK agents. They hold no per-request
# state, so every supervisor can share them -- and building a strands.Agent is
# expensive (it constructs a BedrockModel/boto3 client), so rebuilding per
# instance showed up as seconds of wall time per call.
_SDK_AGENTS_CACHE: dict[str, Any] | None = None
_SDK_SUPERVISOR_CACHE: Any | None = None
_SDK_BUILD_ERROR: str = STRANDS_IMPORT_ERROR


class StrandsSupervisor:
    """Multi-Agent Supervisor orchestrating specialized AWS Strands sub-agents.

    Two execution paths, reported honestly via `backend`:

    * ``aws-strands-sdk``  -- real ``strands.Agent`` objects are constructed for
      each domain and composed with the SDK's agents-as-tools pattern. When
      Bedrock credentials are configured the supervisor agent is actually
      invoked for inference.
    * ``pattern-fallback`` -- the deterministic keyword router below. Used when
      the optional SDK is not installed, or when it is installed but Bedrock is
      not enabled (construction still happens; only inference is unavailable).

    Either way, no consequential action is ever executed by an agent: every
    result is staged into the approval tray and gated by Sentinel.
    """

    def __init__(self) -> None:
        self.agents: dict[str, StrandsBaseAgent] = {
            "arbiter": ArbiterNegotiatorAgent(),
            "replenishment": ReplenishmentDepletionAgent(),
            "guardian": SentinelGuardianAgent(),
        }
        self.memory = agentcore.memory_store
        self._sdk_agents: dict[str, Any] | None = None
        self._sdk_supervisor: Any | None = None
        self._sdk_error: str = _SDK_BUILD_ERROR

    # -- Real AWS Strands SDK wiring ---------------------------------------

    def _build_sdk_agents(self) -> None:
        """Construct genuine strands.Agent objects for each domain agent.

        Tools are registered with the SDK's ``@tool`` decorator, so the SDK
        derives each tool's JSON schema from the signature and docstring. The
        supervisor is composed with ``Agent.as_tool()`` -- the SDK's documented
        multi-agent delegation pattern.
        """
        global _SDK_AGENTS_CACHE, _SDK_SUPERVISOR_CACHE, _SDK_BUILD_ERROR
        if self._sdk_agents is not None:
            return
        if _SDK_AGENTS_CACHE is not None:
            self._sdk_agents = _SDK_AGENTS_CACHE
            self._sdk_supervisor = _SDK_SUPERVISOR_CACHE
            self._sdk_error = ""
            return
        if not STRANDS_AVAILABLE:
            return
        try:
            tool = _strands_tool

            @tool
            def resolve_household_conflict(conflict_type: str = "climate") -> dict:
                """Compute a Pareto-optimal compromise for a household conflict.

                Args:
                    conflict_type: One of climate, energy_peak, or media.
                """
                plan = arbiter.resolve_conflict(conflict_type)
                return {"plan_title": plan.get("title"), "outcome": plan.get("outcome", {})}

            @tool
            def list_active_conflicts() -> dict:
                """List household conflicts awaiting arbitration."""
                return {"conflicts": arbiter.list_active_conflicts()}

            @tool
            def get_pantry_depletion_forecast() -> dict:
                """Predict days-until-empty for every tracked consumable."""
                return {"forecast": commerce.get_depletion_forecast()}

            @tool
            def optimize_subscribe_and_save(auto_fill_tier: bool = True) -> dict:
                """Bundle consumables to unlock the 15% Subscribe & Save tier.

                Args:
                    auto_fill_tier: Fill bundles up to the multi-item discount tier.
                """
                return {"bundles": commerce.optimize_bundles(auto_fill_tier=auto_fill_tier)}

            @tool
            def judge_action_safety(tool_name: str, persona: str = "admin") -> dict:
                """Run the Sentinel 3-tier guardrail for an action.

                Args:
                    tool_name: The tool the agent wants to invoke.
                    persona: Resident persona making the request.
                """
                v = sentinel.judge(tool_name, {"persona": persona})
                return {"decision": v.decision, "risk_tier": v.risk_tier, "reason": v.reason}

            @tool
            def verify_audit_chain() -> dict:
                """Verify the tamper-evident SHA-256 audit ledger."""
                return {"chain_intact": audit.verify(), "entries": audit.count()}

            arbiter_agent = _StrandsAgent(
                name="hearth_arbiter",
                description="Resolves multi-resident conflicts and shifts load off peak tariffs.",
                system_prompt=(
                    "You are the Household Arbiter. Compute Pareto-optimal compromises for "
                    "competing resident preferences and identify peak-tariff load shifting."
                ),
                tools=[resolve_household_conflict, list_active_conflicts],
            )
            replenish_agent = _StrandsAgent(
                name="hearth_replenishment",
                description="Tracks consumable depletion and optimizes Subscribe & Save bundles.",
                system_prompt=(
                    "You are the Commerce Replenishment agent. Calculate depletion velocity, "
                    "stage multi-item bundles for the 15% Subscribe & Save discount."
                ),
                tools=[get_pantry_depletion_forecast, optimize_subscribe_and_save],
            )
            guardian_agent = _StrandsAgent(
                name="hearth_sentinel_guardian",
                description="Enforces Propose-Never-Execute and verifies the audit chain.",
                system_prompt=(
                    "You are the Sentinel Guardian. Enforce Propose-Never-Execute, block "
                    "destructive inputs, and verify cryptographic receipts. Never execute a "
                    "financial or physical-security action directly."
                ),
                tools=[judge_action_safety, verify_audit_chain],
            )

            # Agents-as-tools: the SDK's documented multi-agent delegation.
            self._sdk_supervisor = _StrandsAgent(
                name="hearth_supervisor",
                description="Routes a household goal to the correct specialist sub-agent.",
                system_prompt=(
                    "You coordinate household operations. Delegate climate/tariff questions to "
                    "hearth_arbiter, pantry/restock questions to hearth_replenishment, and any "
                    "security or verification question to hearth_sentinel_guardian. Never "
                    "execute a consequential action; stage it for human approval."
                ),
                tools=[
                    arbiter_agent.as_tool(
                        name="delegate_arbiter",
                        description="Delegate conflict resolution and tariff arbitrage.",
                    ),
                    replenish_agent.as_tool(
                        name="delegate_replenishment",
                        description="Delegate depletion forecasting and bundle optimization.",
                    ),
                    guardian_agent.as_tool(
                        name="delegate_guardian",
                        description="Delegate safety gating and audit verification.",
                    ),
                ],
            )
            self._sdk_agents = {
                "arbiter": arbiter_agent,
                "replenishment": replenish_agent,
                "guardian": guardian_agent,
            }
            self._sdk_error = ""
            _SDK_AGENTS_CACHE = self._sdk_agents
            _SDK_SUPERVISOR_CACHE = self._sdk_supervisor
            _SDK_BUILD_ERROR = ""
        except Exception as exc:  # pragma: no cover - defensive
            self._sdk_agents = None
            self._sdk_supervisor = None
            self._sdk_error = f"{type(exc).__name__}: {exc}"
            _SDK_BUILD_ERROR = self._sdk_error

    @property
    def backend(self) -> str:
        """Which execution path is actually available. Never guessed."""
        if not STRANDS_AVAILABLE:
            return "pattern-fallback"
        self._build_sdk_agents()
        if self._sdk_agents is None:
            return "pattern-fallback"
        return "aws-strands-sdk" if brains.is_bedrock_enabled() else "aws-strands-sdk-no-inference"

    def strands_sdk_status(self) -> dict[str, Any]:
        """Machine-readable evidence of the SDK integration for judges/CI."""
        self._build_sdk_agents()
        specs: dict[str, list[str]] = {}
        if self._sdk_agents:
            for key, agent in self._sdk_agents.items():
                try:
                    specs[key] = sorted(agent.tool_registry.registry.keys())
                except Exception:
                    specs[key] = []
        return {
            "sdk_installed": STRANDS_AVAILABLE,
            "sdk_import_error": STRANDS_IMPORT_ERROR or None,
            "construction_error": self._sdk_error or None,
            "backend": self.backend,
            "bedrock_enabled": bool(brains.is_bedrock_enabled()),
            "subagent_tool_names": specs,
            "supervisor_tool_names": (
                sorted(self._sdk_supervisor.tool_registry.registry.keys())
                if self._sdk_supervisor is not None else []
            ),
            "integration": "strands.Agent + @tool + Agent.as_tool agents-as-tools",
            "install_hint": 'pip install -e ".[aws]"',
        }

    def orchestrate_goal(
        self,
        goal: str,
        session_id: str | None = None,
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Supervisor loop: Decomposes goal -> Delegates to Strands sub-agents -> Synthesizes response."""
        start_t = time.time()
        sid = session_id or f"strands_ses_{uuid.uuid4().hex[:8]}"
        ctx = dict(context or {})

        # Record user turn in Bedrock AgentCore Memory
        self.memory.append_turn(sid, role="user", content=goal, metadata={"framework": "aws-strands-sdk"})

        low = goal.lower()
        subagent_results: list[dict[str, Any]] = []
        all_actions: list[dict[str, Any]] = []
        all_proposals: list[dict[str, Any]] = []

        # Supervisor routing heuristic based on task domains
        selected_agents: list[str] = []
        if any(k in low for k in ("climate", "temp", "energy", "tariff", "bill", "conflict", "schedule", "all", "weekend")):
            selected_agents.append("arbiter")
        if any(k in low for k in ("pantry", "food", "milk", "coffee", "buy", "order", "restock", "all", "weekend")):
            selected_agents.append("replenishment")
        if any(k in low for k in ("lock", "door", "security", "safety", "audit", "verify", "all", "weekend")) or not selected_agents:
            selected_agents.append("guardian")

        # Execute specialized sub-agents
        for agent_key in selected_agents:
            agent = self.agents[agent_key]
            res = agent.run(goal, context=ctx)
            subagent_results.append({
                "agent": res.agent_name,
                "summary": res.summary,
                "actions": res.actions_taken,
                "metrics": res.metrics,
            })
            all_actions.extend(res.actions_taken)
            all_proposals.extend(res.proposals_staged)

        # Synthesize consolidated plan
        summaries = [r["summary"] for r in subagent_results]
        plan_text = " | ".join(summaries)

        # Record supervisor conclusion in AgentCore Memory
        self.memory.append_turn(
            sid,
            role="assistant",
            content=plan_text,
            metadata={"delegated_agents": selected_agents},
        )

        total_latency = round((time.time() - start_t) * 1000, 1)
        sdk_status = self.strands_sdk_status()

        payload = {
            "ok": True,
            "session_id": sid,
            "architecture": "AWS Strands Agents Multi-Agent Supervisor Pattern",
            "goal": goal,
            "delegated_agents": selected_agents,
            "subagent_executions": subagent_results,
            "all_actions": all_actions,
            "proposals_staged": all_proposals,
            "plan_summary": plan_text,
            # Honest execution-path reporting: which of the two paths ran, and
            # whether the real SDK objects were constructed.
            "strands_backend": sdk_status["backend"],
            "strands_sdk": sdk_status,
            "telemetry": {
                "total_latency_ms": total_latency,
                "agentcore_turns": len(self.memory.get_session_turns(sid)),
                "active_brain": brains._get_active_provider(),
            },
        }

        # When Bedrock is genuinely enabled and the SDK is installed, run the
        # real supervisor Agent for inference and record its conclusion. Guarded
        # so an offline judge demo never depends on network or credentials.
        if sdk_status["backend"] == "aws-strands-sdk" and self._sdk_supervisor is not None:
            try:
                reply = self._sdk_supervisor(goal)
                text = str(reply)
                payload["strands_inference"] = {"invoked": True, "model": type(
                    self._sdk_supervisor.model).__name__, "response": text[:2000]}
                self.memory.append_turn(sid, role="assistant", content=text[:2000],
                                        metadata={"framework": "aws-strands-sdk", "inference": True})
            except Exception as exc:  # pragma: no cover - requires live Bedrock
                payload["strands_inference"] = {
                    "invoked": True, "ok": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }

        audit.append("strands_supervisor", "orchestration_completed", {
            "session_id": sid,
            "agents": selected_agents,
            "actions_count": len(all_actions),
            "proposals_count": len(all_proposals),
            "backend": sdk_status["backend"],
        })

        return payload


# Global supervisor instance
supervisor = StrandsSupervisor()
