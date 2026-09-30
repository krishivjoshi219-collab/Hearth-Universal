"""Sentinel: Glass-box AI Safety & Guardrails Engine.
Enforces a 3-tier security posture:
- ALLOW: Safe, read-only queries and context lookups.
- ASK: Consequential actions (money, smart home physical actuation, orders) routed to the Human Approval Tray.
- DENY: Hard-blocked adversarial prompts, shell commands, credential exfiltration, and unauthorized fund transfers.
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
    (r"rm\s+(-[a-zA-Z]*r[a-zA-Z]*f|-[a-zA-Z]*f[a-zA-Z]*r|\s+-rf)\s+[/~*]", "Destructive filesystem deletion (rm -rf)"),
    (r"\b(mkfs|dd\s+if=|fdisk|parted)\b", "Disk formatting / partition alteration"),
    (r":\(\)\{:\|:\};:", "Fork-bomb attack pattern"),
    (r"\b(shutdown|poweroff|reboot|init\s+0)\b", "Host system termination command"),
    (r"\b(curl|wget|nc|netcat)\s+.*\b(bash|sh|python)\b", "Remote code download and execution pipe"),
    (r"(DROP\s+TABLE|TRUNCATE\s+TABLE|DELETE\s+FROM\s+\w+\s*;|1=1)", "SQL injection / destructive database statement"),
    (r"(wire\s+money|send\s+\$?\d+|transfer\s+\$?\d+|pay\s+\$?\d+)", "Direct unapproved currency transfer"),
    (r"(ignore\s+(all\s+)?previous\s+instructions|system\s+prompt\s+override|reveal\s+(api\s+)?key)", "Adversarial prompt injection attempt"),
]

# Read-only and safe operations permitted autonomously
ALLOW_TOOLS = {
    "memory_query",
    "memory_remember",
    "home_get_state",
    "inbox_scan",
    "goals_advance",
    "planner_orchestrate",
    "actions_list_proposals",
    "commerce_list_inventory",
    "commerce_scan_deals",
    "audit_verify",
}

# Operations that change real-world state or household settings (require user approval)
ASK_TOOLS = {
    "actions_propose",
    "home_set_scene",
    "home_routine",
    "home_toggle_lock",
    "goals_create",
    "commerce_propose_order",
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

    # Serialize arguments for deep pattern inspection
    blob = f"{tool} {args}"

    # 2. Check for adversarial / destructive patterns
    for pat, desc in DENY_PATTERNS:
        if re.search(pat, blob, re.IGNORECASE):
            return Verdict("deny", f"Security violation: {desc}", "tier-3", f"pattern:{pat}")

    # 3. Prevent raw Vault secret exfiltration
    if "VAULT_" in blob or "{{vault:" in blob or "sk-live" in blob or "aws_secret_access_key" in blob:
        return Verdict("deny", "Exfiltration blocked: Attempt to read or transmit raw credentials", "tier-3", "vault_exfiltration_policy")

    # 4. Strict egress domain check
    if egress_host and allowlist and egress_host not in allowlist:
        return Verdict("deny", f"Egress blocked: Destination host '{egress_host}' is not in approved registry", "tier-3", "strict_egress_policy")

    # 5. Consequential tools require Human-In-The-Loop approval tray
    if tool in ASK_TOOLS:
        return Verdict("ask", f"Consequential action '{tool}' requires explicit human verification via approval tray", "tier-2", "human_gating_policy")

    # 6. Default to allow for registered safe tools
    if tool in ALLOW_TOOLS:
        return Verdict("allow", "Read-only or safe local query validated", "tier-1", "autonomous_allow_policy")

    return Verdict("ask", f"Unrecognized tool '{tool}' defaults to human verification", "tier-2", "default_fail_safe")
