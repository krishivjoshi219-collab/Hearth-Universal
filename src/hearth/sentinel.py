"""Sentinel: Glass-box AI Safety & Guardrails Engine.
Enforces a 3-tier security posture:
- ALLOW (tier-1): Safe reads AND reversible comfort actions (lights, climate,
  scenes, engaging locks, goals). These execute autonomously — nobody should
  have to approve dimming the lights.
- ASK (tier-2): Irreversible or consequential actions (UNLOCKING doors, moving
  money, placing orders, cancelling services). These must be staged as proposals
  and execute only on an approved proposal. Enforcement is fail-closed.
- DENY (tier-3): Hard-blocked adversarial prompts, shell commands, credential
  exfiltration, and unauthorized fund transfers.
"""
from __future__ import annotations
from dataclasses import dataclass
import re

@dataclass
class Verdict:
    decision: str  # allow | ask | deny
    reason: str
    risk_tier: str  # tier-1 (safe) | tier-2 (gated) | tier-3 (critical)
    matched_rule: str = ""


# Malicious and dangerous shell / prompt-injection / exfiltration patterns
DENY_PATTERNS = [
    (r"\brm\s+(?:-[a-zA-Z0-9_-]+\s+)*.*(?:-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|-r\s+-f|-f\s+-r|--recursive|--force).*(?:[/~*.]|$)", "Destructive filesystem deletion (rm -rf)"),
    (r"\b(mkfs|dd\s+if=|fdisk|parted)\b", "Disk formatting / partition alteration"),
    (r":\(\)\{:\|:\};:", "Fork-bomb attack pattern"),
    (r"\b(shutdown|poweroff|reboot|init\s+0)\b", "Host system termination command"),
    (r"\b(curl|wget|nc|netcat)\s+.*\b(bash|sh|python)\b", "Remote code download and execution pipe"),
    (r"(DROP\s+TABLE|TRUNCATE\s+TABLE|DELETE\s+FROM\s+\w+\s*;|1=1)", "SQL injection / destructive database statement"),
    (r"(wire\s+money|send\s+\$?\d+|transfer\s+\$?\d+|pay\s+\$?\d+)", "Direct unapproved currency transfer"),
    (r"(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt\s+override|reveal\s+(api\s+)?key)", "Adversarial prompt injection attempt"),
]

# Tier-1: reads + reversible comfort actions execute autonomously
ALLOW_TOOLS = {
    "memory_query",
    "memory_remember",
    "home_get_state",
    "home_update_device",
    "home_set_scene",
    "home_routine",
    "inbox_scan",
    "goals_create",
    "goals_advance",
    "goals_list",
    "planner_orchestrate",
    "actions_list_proposals",
    "commerce_list_inventory",
    "commerce_scan_deals",
    "commerce_depletion_forecast",
    "commerce_optimize_bundles",
    "commerce_available_delivery_slots",
    "commerce_reschedule_delivery",
    "commerce_delivery_tracker",
    "commerce_scan_barcode",
    "family_arbiter_resolve",
    "timemachine_forecast",
    "mcp_app_subscription_roi",
    "mcp_app_lighting_designer",
    "mcp_app_pantry_restock",
    "audit_verify",
    "web_search",
    "web_fetch",
    "workspace_read",
    "workspace_list",
}

# Tier-2: consequential actions. Staged as proposals; execute ONLY on approval.
# NOTE: home_toggle_lock is judged context-sensitively below (lock=allow, unlock=ask).
ASK_TOOLS = {
    "actions_propose",
    "home_toggle_lock",
    "commerce_propose_order",
    "workspace_exec",
    "workspace_write",
}

# Strictly forbidden operations that must never execute directly
DENY_TOOLS = {
    "actions_execute_direct",
    "shell_exec_raw",
    "eval_code_raw",
    "wire_funds_direct",
    "delete_all_memory",
}


def judge(tool: str, args: dict | None = None, egress_host: str = "", allowlist: tuple = ()) -> Verdict:
    """Evaluate an action against Sentinel security policies."""
    args = args or {}
    
    # 1. Direct tool blacklist
    if tool in DENY_TOOLS:
        return Verdict("deny", f"Tool '{tool}' is in the forbidden execution tier", "tier-3", "deny_tool_policy")

    # Child persona guardrail: children cannot unlock doors, modify finances, or execute commands
    persona = str(args.get("persona") or args.get("persona_id") or "").strip().lower()
    if persona in ("child", "leo", "kid", "child_mode", "child_profile"):
        if tool in ("home_toggle_lock", "actions_propose", "commerce_propose_order", "workspace_write", "workspace_exec"):
            return Verdict("deny", "Child safety guardrail: Child profile 'Leo' is restricted to safe ambient comfort actions. Ask an adult to authorize financial or physical security changes.", "tier-3", "child_safety_policy")

    # Path safety guardrail: detect path traversal and absolute path escapes in file/workspace operations
    for key in ("path", "file", "filepath", "filename"):
        val = args.get(key)
        if isinstance(val, str):
            sval = val.strip()
            if "\x00" in sval or sval.startswith(("/", "~")) or ".." in sval.split("/") or ".." in sval.split("\\"):
                return Verdict("deny", "Path safety violation: path must be relative and inside the workspace jail", "tier-3", "path_traversal_policy")

    # Serialize arguments for deep pattern inspection
    blob = f"{tool} {args}"

    # 2. Check for adversarial / destructive patterns
    for pat, desc in DENY_PATTERNS:
        if re.search(pat, blob, re.IGNORECASE):
            return Verdict("deny", f"Security violation: {desc}", "tier-3", f"pattern:{pat}")

    # 3. Prevent raw Vault secret exfiltration
    if (re.search(r"\{\{\s*vault:[^}]+\}\}", blob, re.IGNORECASE) or
        re.search(r"\bvault_[a-z0-9_]+", blob, re.IGNORECASE) or
        re.search(r"VAULT_", blob) or "{{vault:" in blob or "sk-live" in blob or
        re.search(r"aws_secret_access_key|aws_session_token", blob, re.IGNORECASE)):
        return Verdict("deny", "Exfiltration blocked: Attempt to read or transmit raw credentials", "tier-3", "vault_exfiltration_policy")

    # 4. Strict egress domain check
    if egress_host and allowlist and egress_host not in allowlist:
        return Verdict("deny", f"Egress blocked: Destination host '{egress_host}' is not in approved registry", "tier-3", "strict_egress_policy")

    # 5. Direction-sensitive lock policy: engaging a lock is safe comfort,
    # DISENGAGING a lock is consequential and must be gated.
    if tool == "home_toggle_lock" and args.get("locked", True) is False:
        return Verdict("ask", "Unlocking a door requires explicit human verification via approval tray", "tier-2", "unlock_gating_policy")
    if tool == "home_toggle_lock":
        return Verdict("allow", "Engaging a lock is a safe comfort action", "tier-1", "lock_autonomous_policy")

    # 6. Consequential tools require Human-In-The-Loop approval tray
    if tool in ASK_TOOLS:
        return Verdict("ask", f"Consequential action '{tool}' requires explicit human verification via approval tray", "tier-2", "human_gating_policy")

    # 7. Default to allow for registered safe tools
    if tool in ALLOW_TOOLS:
        return Verdict("allow", "Safe comfort action validated", "tier-1", "autonomous_allow_policy")

    return Verdict("ask", f"Unrecognized tool '{tool}' defaults to human verification", "tier-2", "default_fail_safe")
