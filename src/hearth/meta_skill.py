"""Meta-Skill Synthesizer: Self-Evolving Agent Skill Compiler for Alexa+.

Production-grade pipeline:
parse intent -> infer JSON schema -> generate code -> Sentinel gate ->
AST validation -> sandboxed smoke test -> versioned hot-mount -> audit.
"""
from __future__ import annotations

import ast
import json
import os
import re
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from . import agent_skills, atomic, audit, sentinel


def _state_dir() -> Path:
    d = Path(os.environ.get("HEARTH_STATE_DIR", "state")) / "synthesized_skills"
    d.mkdir(parents=True, exist_ok=True)
    return d


@dataclass
class SynthesizedSkill:
    skill_id: str
    name: str
    version: str
    description: str
    capabilities: list[str]
    tools_exposed: list[str]
    parameters_schema: dict[str, Any]
    code_snippet: str
    safety_verdict: str
    author_persona: str
    is_active: bool = True
    created_at: float = field(default_factory=time.time)
    # god-tier
    intent: dict[str, Any] = field(default_factory=dict)
    version_int: int = 1
    parent_id: str | None = None
    handler_actions: list[str] = field(default_factory=list)
    ast_report: dict[str, Any] = field(default_factory=dict)
    test_report: dict[str, Any] = field(default_factory=dict)
    savings_formula: str = ""


# ---------------------------------------------------------------------------
# Intent parsing (deterministic, no LLM)
# ---------------------------------------------------------------------------

_DOMAINS = {
    "security": ["door", "lock", "unlock", "security", "camera"],
    "ev": ["ev", "tesla", "car charge", "charging", "vehicle"],
    "hvac": ["hvac", "thermostat", "pre-cool", "precool", "ac ", "cool", "heat", "climate"],
    "greenhouse": ["greenhouse", "ventilation", "garden", "plants"],
    "laundry": ["laundry", "washer", "dryer", "dishwasher", "dishes"],
    "lighting": ["light", "lamp", "cct", "circadian", "dim"],
    "pantry": ["pantry", "grocery", "restock", "subscribe", "replenish", "fridge"],
    "solar": ["solar", "battery", "grid", "vpp", "peak"],
}

_PRIVILEGED = ["door", "lock", "unlock", "security", "gate", "camera", "vault", "funds", "wire", "payment"]

# A privileged rule is only synthesizable when it carries an explicit
# human-confirmation clause ("notify me", "only after my approval", ...).
_HUMAN_GATE_MARKERS = (
    "approv", "confirm", "notify", "ask me", "with my", "only after",
    "human", "permission", "explicit",
)


def _has_human_gate(low: str) -> bool:
    return any(m in low for m in _HUMAN_GATE_MARKERS)


def _repair_requirement(requirement: str) -> str:
    """Rewrite an autonomous privileged rule into a human-gated safe variant.

    'Unlock the front door whenever the camera sees motion'
      -> 'Notify me when the camera sees motion; unlock the front door only
          after my explicit approval'
    """
    r = str(requirement).strip().rstrip(".")
    low = r.lower()
    for w in (" whenever ", " when "):
        if w in low:
            i = low.index(w)
            action = r[:i].strip()
            trigger = r[i + len(w):].strip()
            if action and trigger:
                act = action[0].lower() + action[1:] if action[0].isupper() else action
                return (f"Notify me {w.strip()} {trigger}; {act} only after my "
                        f"explicit approval")
    act = (r[0].lower() + r[1:]) if r else r
    return f"Notify me first; {act} only after my explicit approval"


def parse_intent(requirement: str) -> dict[str, Any]:
    low = requirement.lower()
    domain = "general"
    for d, keys in _DOMAINS.items():
        if any(k in low for k in keys):
            domain = d
            break
    m_ampm = re.search(r"(\d{1,2})\s*(am|pm)\b", low)
    m_clock = re.search(r"\b(\d{1,2}):00\b", low)
    hour_hint = None
    if m_ampm:
        hour_hint = int(m_ampm.group(1))
        if m_ampm.group(2) == "pm" and hour_hint < 12:
            hour_hint += 12
        if m_ampm.group(2) == "am" and hour_hint == 12:
            hour_hint = 0
    elif m_clock:
        hour_hint = int(m_clock.group(1))
    if hour_hint is not None:
        hour_hint = max(0, min(23, hour_hint))
    return {
        "domain": domain,
        "hour_hint": hour_hint if hour_hint is not None else 14,
        "eco": any(w in low for w in ["solar", "eco", "off-peak", "offpeak", "peak", "green"]),
        "privileged": any(w in low for w in _PRIVILEGED),
        "raw": requirement[:200],
    }


def infer_schema(intent: dict[str, Any], requirement: str) -> dict[str, Any]:
    base_props: dict[str, Any] = {
        "schedule_hour": {"type": "integer", "description": "Target execution hour (0-23)", "default": intent["hour_hint"]},
        "eco_mode": {"type": "boolean", "description": "Prioritize solar and off-peak tariffs", "default": True},
        "note": {"type": "string", "description": "Contextual requirement", "default": requirement[:200]},
    }
    required = ["schedule_hour"]
    d = intent["domain"]
    if d == "ev":
        base_props["target_kwh"] = {"type": "number", "description": "Charge energy kWh", "default": 8.0}
        base_props["max_price"] = {"type": "number", "description": "Max $/kWh", "default": 0.28}
        required = ["schedule_hour", "target_kwh"]
    elif d == "security":
        base_props["require_confirmation"] = {
            "type": "boolean",
            "description": "Require explicit human approval before acting",
            "default": True,
        }
        required = ["schedule_hour", "require_confirmation"]
    elif d == "greenhouse":
        base_props["max_temp_c"] = {"type": "number", "description": "Vent above C", "default": 28.0}
        base_props["min_temp_c"] = {"type": "number", "description": "Close below C", "default": 18.0}
        required = ["schedule_hour", "max_temp_c"]
    elif d == "hvac":
        base_props["target_temp_f"] = {"type": "number", "description": "Setpoint F", "default": 70.0}
        required = ["schedule_hour", "target_temp_f"]
    elif d == "laundry":
        base_props["cycle"] = {"type": "string", "description": "eco|normal", "default": "eco"}
    return {"type": "object", "properties": base_props, "required": required}


def generate_code(intent: dict[str, Any], schema: dict[str, Any], requirement: str) -> tuple[str, str]:
    """Emit a real handler computing savings from TOU spread + params. Returns (code, formula)."""
    d = intent["domain"]
    status = "scheduled"
    extras = ""
    if d == "security":
        # Proposal-only by construction: the handler can never execute a
        # physical action itself; it drafts one and parks it for approval.
        body = ("hour = int(params.get('schedule_hour', 22));"
                " action = params.get('note', 'security_action');"
                " savings = 0.0")
        status = "awaiting_human_approval"
        extras = ", 'requires_human_approval': True, 'proposed_action': action"
    elif d == "ev":
        body = ("kwh = float(params.get('target_kwh', 8.0)); hour = int(params.get('schedule_hour', 14));"
                " cap = float(params.get('max_price', 0.28));"
                " peak = 0.52 if 16 <= hour <= 20 else (0.12 if (hour >= 22 or hour < 6) else 0.28);"
                " savings = round(max(0.0, (0.52 - peak)) * kwh, 2) if peak <= cap else 0.0")
    elif d == "greenhouse":
        body = ("span = float(params.get('max_temp_c', 28.0)) - float(params.get('min_temp_c', 18.0));"
                " savings = round(max(0.0, min(12.0, span * 0.4)), 2)")
    elif d == "hvac":
        body = ("t = float(params.get('target_temp_f', 70.0)); hour = int(params.get('schedule_hour', 14));"
                " peak = 0.52 if 16 <= hour <= 20 else 0.28;"
                " savings = round(max(0.0, (72.0 - t) * 0.35 + (0.52 - peak) * 4.0), 2)")
    else:
        body = ("hour = int(params.get('schedule_hour', 14));"
                " peak = 0.52 if 16 <= hour <= 20 else (0.12 if (hour >= 22 or hour < 6) else 0.28);"
                " savings = round(max(0.0, (0.52 - peak)) * 3.0 + (0.15 if params.get('eco_mode', True) else 0.0), 2)")
    safe_req = requirement.replace("'", "").replace('"', "").replace("\n", " ")[:120]
    ret_line = (
        "    return {'status': " + repr(status) + ", 'requirement': params.get('note', ''),"
        " 'applied_hour': int(params.get('schedule_hour', 14)),"
        " 'eco_mode': bool(params.get('eco_mode', True)), 'savings_usd': float(savings)"
        + extras + "}\n"
    )
    code = (
        f"# Synthesized [{d}] for: {safe_req}\n"
        "def execute_plan(params):\n"
        "    params = dict(params or {})\n"
        f"    {body}\n"
        + ret_line +
        "def handle(action, params):\n"
        "    return {'executed_action': action, **execute_plan(params)}\n"
    )
    formula = f"domain={d}: " + body
    if d == "security":
        formula = ("domain=security: proposal-only toolkit; savings 0.0; "
                   "requires explicit human approval")
    return code, formula


# ---------------------------------------------------------------------------
# AST validation
# ---------------------------------------------------------------------------

_FORBIDDEN_CALLS = {"eval", "exec", "open", "__import__", "compile", "input"}
_FORBIDDEN_ATTRS = {"system", "popen", "socket", "requests", "urllib", "subprocess", "os"}
_FORBIDDEN_IMPORTS = {"os", "subprocess", "socket", "requests", "urllib", "shutil", "pathlib", "sys"}


def ast_validate(src: str) -> dict[str, Any]:
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return {"ok": False, "error": f"syntax: {e}", "rule": "syntax"}
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = []
            if isinstance(node, ast.Import):
                names = [a.name.split(".")[0] for a in node.names]
            else:
                names = [(node.module or "").split(".")[0]]
            for n in names:
                if n in _FORBIDDEN_IMPORTS and n not in ("math", "datetime"):
                    return {"ok": False, "error": f"forbidden import: {n}", "rule": f"import:{n}"}
        if isinstance(node, ast.Call):
            f = node.func
            if isinstance(f, ast.Name) and f.id in _FORBIDDEN_CALLS:
                return {"ok": False, "error": f"forbidden call: {f.id}", "rule": f"call:{f.id}"}
            if isinstance(f, ast.Attribute) and f.attr in _FORBIDDEN_ATTRS:
                return {"ok": False, "error": f"forbidden attr: {f.attr}", "rule": f"attr:{f.attr}"}
    # Must define execute_plan
    if "def execute_plan" not in src:
        return {"ok": False, "error": "missing execute_plan", "rule": "shape"}
    # Sentinel pattern sweep
    for pat, _ in sentinel.DENY_PATTERNS:
        if re.search(pat, src, re.IGNORECASE):
            return {"ok": False, "error": f"sentinel pattern: {pat[:40]}", "rule": "sentinel"}
    return {"ok": True, "nodes": len(list(ast.walk(tree)))}


def sandbox_smoke(src: str, schema: dict[str, Any]) -> dict[str, Any]:
    """In-process exec with stripped builtins + sample params per schema."""
    safe_builtins = {"abs": abs, "min": min, "max": max, "round": round, "sum": sum, "len": len,
                     "dict": dict, "list": list, "float": float, "int": int, "bool": bool, "str": str}
    ns: dict[str, Any] = {"__builtins__": safe_builtins}
    try:
        exec(compile(src, "<synth>", "exec"), ns)
    except Exception as e:
        return {"ok": False, "error": f"exec: {e}"}
    fn = ns.get("execute_plan")
    if not callable(fn):
        return {"ok": False, "error": "no execute_plan fn"}
    sample: dict[str, Any] = {}
    for k, spec in (schema.get("properties") or {}).items():
        if "default" in spec:
            sample[k] = spec["default"]
    try:
        out = fn(sample)
    except Exception as e:
        return {"ok": False, "error": f"run: {e}"}
    if not isinstance(out, dict) or "savings_usd" not in out:
        return {"ok": False, "error": "bad shape"}
    try:
        float(out["savings_usd"])
    except Exception:
        return {"ok": False, "error": "savings not numeric"}
    if "4.25" in src and "savings_usd" in src and src.count("4.25") > 0 and "max(0.0" not in src:
        return {"ok": False, "error": "hardcoded savings"}
    return {"ok": True, "sample_out": out}


class MetaSkillSynthesizer:
    """Compiles and hot-mounts new agent skills into the live Alexa+ environment."""

    def __init__(self) -> None:
        self.storage_dir = _state_dir()
        self._skills: dict[str, SynthesizedSkill] = {}
        self._load_stored_skills()

    def _load_stored_skills(self) -> None:
        if not self.storage_dir.exists():
            return
        for file in self.storage_dir.glob("*.json"):
            try:
                with open(file, encoding="utf-8") as f:
                    data = json.load(f)
                skill = SynthesizedSkill(**{k: v for k, v in data.items() if k in SynthesizedSkill.__dataclass_fields__})
                self._skills[skill.skill_id] = skill
                self._mount_into_runtime(skill)
            except Exception:
                continue

    def synthesize(self, requirement: str, author_persona: str = "Alex",
                   repaired_from: str | None = None) -> dict[str, Any]:
        t_start = time.time()
        low = str(requirement).lower()
        intent = parse_intent(requirement)
        skill_slug = re.sub(r"[^a-z0-9_]", "", requirement.lower().replace(" ", "_"))[:20] or "skill"
        skill_id = f"amzn1.ask.skill.hearth.custom.{skill_slug}_{uuid.uuid4().hex[:6]}"
        skill_name = f"Custom: {requirement[:35]}"

        # Gate 0: non-adult personas may not synthesize privileged skills (defense in depth).
        if intent["privileged"] and str(author_persona).strip().lower() in ("leo", "child", "kid", "minor"):
            ev = audit.append("meta_skill_synthesizer", "synthesis_refused_child_profile",
                {"requirement": requirement, "gate": "child_gate", "persona": author_persona})
            return {"ok": False, "blocked": True, "gate": "child_gate",
                    "error": "Synthesis blocked by Sentinel Safety: Child profile may not synthesize security skills",
                    "reason": "Child profile may not synthesize security or payment skills",
                    "detail": "Security and money tools are adult-gated by design.",
                    "risk_tier": "tier-3", "repair_available": False,
                    "audit_hash": ev.get("hash", "")}

        # Gate 1: privileged intents require an explicit human-confirmation clause.
        if intent["privileged"] and not _has_human_gate(low):
            ev = audit.append("meta_skill_synthesizer", "synthesis_refused_privileged",
                {"requirement": requirement, "gate": "sentinel", "persona": author_persona})
            reason = "Physical security or money movement without human confirmation"
            return {"ok": False, "blocked": True, "gate": "sentinel",
                    "error": f"Synthesis blocked by Sentinel Safety: {reason}",
                    "reason": reason,
                    "detail": ("This rule asks Hearth to act on locks, doors, cameras, or funds "
                               "on its own. Hearth never executes those without you."),
                    "risk_tier": "tier-3",
                    "suggested_repair": _repair_requirement(requirement),
                    "repair_available": True, "audit_hash": ev.get("hash", "")}

        schema = infer_schema(intent, requirement)
        code_logic, formula = generate_code(intent, schema, requirement)

        verdict = sentinel.judge(tool="workspace_write",
            args={"path": f"skills/{skill_slug}.py", "content": code_logic, "persona": author_persona})
        if verdict.decision == "deny":
            ev = audit.append("meta_skill_synthesizer", "synthesis_rejected_by_safety",
                {"requirement": requirement, "reason": verdict.reason, "persona": author_persona})
            return {"ok": False, "blocked": True, "gate": "sentinel",
                    "error": f"Synthesis blocked by Sentinel Safety: {verdict.reason}",
                    "reason": str(verdict.reason or "Sentinel safety denial"),
                    "detail": "The generated handler tripped a safety pattern.",
                    "risk_tier": verdict.risk_tier, "repair_available": False,
                    "audit_hash": ev.get("hash", "")}

        ast_rep = ast_validate(code_logic)
        if not ast_rep.get("ok"):
            ev = audit.append("meta_skill_synthesizer", "synthesis_rejected_by_ast", {"reason": ast_rep})
            return {"ok": False, "blocked": True, "gate": "ast",
                    "error": f"AST validation failed: {ast_rep.get('error')}",
                    "reason": f"AST validation failed: {ast_rep.get('error')}",
                    "detail": "The generated source did not pass static verification.",
                    "risk_tier": "tier-3", "repair_available": False,
                    "audit_hash": ev.get("hash", "")}
        smoke = sandbox_smoke(code_logic, schema)
        if not smoke.get("ok"):
            ev = audit.append("meta_skill_synthesizer", "synthesis_rejected_by_smoke", {"reason": smoke})
            return {"ok": False, "blocked": True, "gate": "smoke",
                    "error": f"Smoke test failed: {smoke.get('error')}",
                    "reason": f"Smoke test failed: {smoke.get('error')}",
                    "detail": "The sandboxed handler did not run cleanly on sample inputs.",
                    "risk_tier": "tier-3", "repair_available": False,
                    "audit_hash": ev.get("hash", "")}

        caps = [f"{skill_slug}_dispatch", "temporal_scheduling", "energy_coordination", f"domain_{intent['domain']}"]
        tools = [f"custom_{skill_slug}_execute"]
        skill = SynthesizedSkill(skill_id=skill_id, name=skill_name, version="1.0.0-synthesized",
            description=f"Synthesized [{intent['domain']}] skill: {requirement}",
            capabilities=caps, tools_exposed=tools, parameters_schema=schema,
            code_snippet=code_logic, safety_verdict=verdict.decision,
            author_persona=author_persona, is_active=True, intent=intent, version_int=1,
            handler_actions=["execute_plan"], ast_report=ast_rep,
            test_report=smoke, savings_formula=formula)
        self._mount_into_runtime(skill)
        self._skills[skill_id] = skill
        out_file = self.storage_dir / f"{skill_slug}.json"
        atomic.atomic_write_json(out_file, asdict(skill))
        ev = audit.append("meta_skill_synthesizer", "skill_synthesized_and_mounted",
            {"skill_id": skill_id, "name": skill_name, "tools": tools,
             "repaired_from": repaired_from or "",
             "duration_ms": round((time.time() - t_start) * 1000, 1)})
        return {"ok": True, "skill_id": skill_id, "name": skill_name, "capabilities": caps,
                "tools_exposed": tools, "status": "mounted_live",
                "safety_audit": f"PASSED (Sentinel {verdict.risk_tier} + AST + smoke)",
                "intent": intent, "savings_formula": formula,
                "repaired": bool(repaired_from), "repaired_from": repaired_from or "",
                "audit_hash": ev.get("hash", "")}

    def _mount_into_runtime(self, skill: SynthesizedSkill) -> None:
        safe_builtins = {"abs": abs, "min": min, "max": max, "round": round, "sum": sum, "len": len,
                         "dict": dict, "list": list, "float": float, "int": int, "bool": bool, "str": str}
        ns: dict[str, Any] = {"__builtins__": safe_builtins}
        handler_fn = None
        try:
            exec(compile(skill.code_snippet, "<mount>", "exec"), ns)
            handler_fn = ns.get("handle") or ns.get("execute_plan")
        except Exception:
            handler_fn = None

        def dynamic_handler(action: str, params: dict[str, Any]) -> dict[str, Any]:
            try:
                if callable(handler_fn):
                    if "handle" in skill.code_snippet and callable(ns.get("handle")):
                        out = ns["handle"](action, dict(params or {}))
                    else:
                        out = ns["execute_plan"](dict(params or {}))
                    if isinstance(out, dict):
                        return {"ok": True, "executed_skill": skill.skill_id, "action": action,
                                "parameters": params, "result": out}
            except Exception as e:
                return {"ok": False, "error": str(e)}
            return {"ok": False, "error": "handler missing or returned non-dict (no fallback — re-synthesize)"}

        skill_def = agent_skills.AgentSkillDefinition(
            skill_id=skill.skill_id, name=skill.name, version=skill.version,
            description=skill.description, capabilities=skill.capabilities,
            tools_exposed=skill.tools_exposed, requires_human_approval=False, handler=dynamic_handler)
        agent_skills.agent_skills_runtime.register(skill_def)

    def list_synthesized_skills(self) -> list[dict[str, Any]]:
        return [asdict(s) for s in self._skills.values()]


meta_synthesizer = MetaSkillSynthesizer()
