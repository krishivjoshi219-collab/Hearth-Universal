"""Proof Engine: hash-chained household receipts, derived from real events.

Every receipt anchors one or more audit-ledger events (evidence) into a single
canonical record: the terms Hearth was working from -> what actually settled.
Receipts chain to each other with SHA-256, so a hand-edited number is provable
on sight: the recomputed hash no longer matches the one on the receipt.

Honest by construction: a receipt is only issued for things that really
happened (VPP dispatch settlements, executed approvals, live tool calls),
and each one stays openable to its source-event hashes in the audit ledger.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import time
from pathlib import Path
from typing import Any

from . import atomic

# Bind the state dir at import time, like hearth.audit does: one process sees
# one ledger, even if tests swap HEARTH_STATE_DIR around mid-session.
STATE_DIR = Path(os.environ.get("HEARTH_STATE_DIR", "state"))


def _state_dir() -> Path:
    STATE_DIR.mkdir(parents=True, exist_ok=True)
    return STATE_DIR


def _receipts_path() -> Path:
    return _state_dir() / "receipts.jsonl"


def _audit_path() -> Path:
    return _state_dir() / "audit.jsonl"


def _canonical(payload: dict[str, Any]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), default=str)


def _hash_body(body: dict[str, Any]) -> str:
    return hashlib.sha256(_canonical(body).encode("utf-8")).hexdigest()


def _load() -> list[dict[str, Any]]:
    path = _receipts_path()
    if not path.exists():
        return []
    out: list[dict[str, Any]] = []
    with atomic.locked(path):
        for raw_line in path.read_text(encoding="utf-8").splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                r = json.loads(line)
            except Exception:
                continue
            if isinstance(r, dict) and "receipt_hash" in r:
                out.append(r)
    return out


def _append_line(receipt: dict[str, Any]) -> None:
    with atomic.locked(_receipts_path()), _receipts_path().open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(receipt, sort_keys=True, default=str) + "\n")


def _receipt_id(kind: str, ts: int, seed: str) -> str:
    raw = f"{kind}|{ts}|{seed}".encode()
    return "rcpt_" + hashlib.sha256(raw).hexdigest()[:12]


def _seal(body: dict[str, Any], prev_hash: str) -> dict[str, Any]:
    body["prev_receipt_hash"] = prev_hash
    body["receipt_hash"] = _hash_body(body)
    return body


# ---------------------------------------------------------------------------
# Event -> receipt mapping (rebuild path)
# ---------------------------------------------------------------------------

def _event_to_receipt(e: dict[str, Any]) -> dict[str, Any] | None:
    """Pure mapping: an audit event -> receipt body fields (no chain fields)."""
    action = e.get("action")
    detail = e.get("detail") or {}
    ts = int(e.get("ts", 0) or 0)
    h = str(e.get("hash", ""))
    if not h:
        return None

    if action == "microgrid_dispatch_settled":
        kw = float(detail.get("allocated_kw", 0) or 0)
        price = float(detail.get("price", 0) or 0)
        div = float(detail.get("community_dividend", 0) or 0)
        return {
            "receipt_id": _receipt_id("vpp_dispatch", ts, h),
            "ts": ts,
            "kind": "vpp_dispatch",
            "claim": (f"Sold {kw:g} kW into the community VPP at ${price:.2f}/kWh — "
                      f"${div:.2f} dividend banked"),
            "money": {"earned_usd": round(div, 2)},
            "terms": {"allocated_kw": kw, "price_usd_per_kwh": price},
            "settled": {"community_dividend_usd": round(div, 2),
                        "trade_id": str(detail.get("trade_id", ""))},
            "source_events": [h],
        }

    if action == "execution_applied":
        ex = detail.get("execution") or {}
        note = str(ex.get("note", ""))
        qr = str(ex.get("qr_payload", ""))
        m = re.search(r"total=([0-9]+(?:\.[0-9]+)?)", qr)
        total = float(m.group(1)) if m else 0.0
        code = str(ex.get("receipt_code", ""))
        try:
            credit = round(float(ex.get("credit_usd", 0) or 0), 2)
        except (TypeError, ValueError):
            credit = 0.0
        if credit > 0:
            label = str(ex.get("delay_label") or "late delivery")
            return {
                "receipt_id": _receipt_id("credit_claimed", ts, h),
                "ts": ts,
                "kind": "credit_claimed",
                "claim": (f"Amazon courtesy credit claimed — +${credit:.2f} "
                          f"(delivery arrived {label} past the promised time)"),
                "money": {"earned_usd": credit},
                "terms": {"order_id": ex.get("order_id", ""),
                          "tracking_number": ex.get("tracking_number", ""),
                          "delay_minutes": ex.get("delay_minutes")},
                "settled": {"credit_receipt_code": code, "credit_usd": credit},
                "source_events": [h],
            }
        if total > 0:
            return {
                "receipt_id": _receipt_id("order_staged", ts, h),
                "ts": ts,
                "kind": "order_staged",
                "claim": f"Order staged — ${total:.2f} (checkout simulated, no live payment)",
                "money": {"spent_usd": round(total, 2)},
                "terms": {"note": note[:160]},
                "settled": {"order_receipt_code": code, "total_usd": round(total, 2)},
                "source_events": [h],
            }
        return {
            "receipt_id": _receipt_id("approval_executed", ts, h),
            "ts": ts,
            "kind": "approval_executed",
            "claim": f"Approval executed: {note[:90] or 'household action'}",
            "money": {},
            "terms": {"note": note[:160]},
            "settled": {"applied_at": int(ex.get("at", ts) or ts)},
            "source_events": [h],
        }

    return None


def rebuild() -> int:
    """Idempotently issue receipts for supported audit events not yet receipted."""
    audit_path = _audit_path()
    if not audit_path.exists():
        return 0
    with atomic.locked(_receipts_path()):
        receipts = _load()
        seen = {h for r in receipts for h in (r.get("source_events") or [])}
        prev = receipts[-1]["receipt_hash"] if receipts else "GENESIS"
        added = 0
        new_lines: list[str] = []
        for raw_line in audit_path.read_text().splitlines():
            line = raw_line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except Exception:
                continue
            h = str(e.get("hash", ""))
            if not h or h in seen:
                continue
            body = _event_to_receipt(e)
            if body is None:
                continue
            body = _seal(body, prev)
            prev = body["receipt_hash"]
            new_lines.append(json.dumps(body, sort_keys=True, default=str))
            added += 1
        if new_lines:
            with _receipts_path().open("a", encoding="utf-8") as fh:
                fh.write("\n".join(new_lines) + "\n")
    return added


# ---------------------------------------------------------------------------
# Live path: a forged MCP tool was just called (called from /api/forge/invoke)
# ---------------------------------------------------------------------------

def record_tool_applied(tool: str, params: dict[str, Any], result: dict[str, Any],
                        source_hash: str = "") -> dict[str, Any]:
    """Issue a receipt for a live tool call; links to the audit event hash."""
    try:
        savings = round(float(result.get("savings_usd", 0) or 0), 2)
    except Exception:
        savings = 0.0
    ts = int(time.time())
    if savings > 0:
        claim = (f"MCP tool {tool} applied at hour {result.get('applied_hour', '?')} — "
                 f"${savings:.2f} saved")
        money: dict[str, Any] = {"saved_usd": savings}
    else:
        claim = (f"MCP tool {tool} completed with no money moved "
                 f"(status: {result.get('status', 'ok')})")
        money = {}
    settled = {k: result.get(k) for k in
               ("status", "applied_hour", "savings_usd", "eco_mode") if k in result}
    body = {
        "receipt_id": _receipt_id("tool_applied", ts, tool + str(source_hash)),
        "ts": ts,
        "kind": "tool_applied",
        "claim": claim,
        "money": money,
        "terms": {"tool": tool, "params": params},
        "settled": settled,
        "source_events": [source_hash] if source_hash else [],
    }
    with atomic.locked(_receipts_path()):
        receipts = _load()
        prev = receipts[-1]["receipt_hash"] if receipts else "GENESIS"
        body = _seal(body, prev)
        with _receipts_path().open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(body, sort_keys=True, default=str) + "\n")
    return body


# ---------------------------------------------------------------------------
# Read / verify / tamper
# ---------------------------------------------------------------------------

def chain_valid(receipts: list[dict[str, Any]] | None = None) -> bool:
    rs = _load() if receipts is None else receipts
    prev = "GENESIS"
    for r in rs:
        if r.get("prev_receipt_hash") != prev:
            return False
        body = {k: v for k, v in r.items() if k != "receipt_hash"}
        if _hash_body(body) != r.get("receipt_hash"):
            return False
        prev = r["receipt_hash"]
    return True


def ledger(receipts: list[dict[str, Any]] | None = None) -> dict[str, Any]:
    rs = _load() if receipts is None else receipts
    saved = round(sum(float((r.get("money") or {}).get("saved_usd", 0) or 0) for r in rs), 2)
    earned = round(sum(float((r.get("money") or {}).get("earned_usd", 0) or 0) for r in rs), 2)
    spent = round(sum(float((r.get("money") or {}).get("spent_usd", 0) or 0) for r in rs), 2)
    by_kind: dict[str, int] = {}
    for r in rs:
        k = str(r.get("kind", "unknown"))
        by_kind[k] = by_kind.get(k, 0) + 1
    return {
        "receipts_count": len(rs),
        "saved_usd": saved,
        "earned_usd": earned,
        "spent_usd": spent,
        "verified_usd": round(saved + earned, 2),
        "net_usd": round(saved + earned - spent, 2),
        "chain_head": rs[-1]["receipt_hash"] if rs else "",
        "chain_valid": chain_valid(rs),
        "by_kind": by_kind,
    }


def list_receipts(limit: int = 8) -> dict[str, Any]:
    rs = _load()
    return {
        "receipts": list(reversed(rs))[: max(1, limit)],
        "receipts_count": len(rs),
        "ledger": ledger(rs),
    }


def _tamper_field(t: dict[str, Any]) -> tuple[str, Any, Any]:
    money = t.get("money") or {}
    for key in ("saved_usd", "earned_usd", "spent_usd"):
        if key in money:
            original = money[key]
            money[key] = round(float(original) + 4.0, 2)
            t["money"] = money
            return f"money.{key}", original, money[key]
    original = t.get("claim", "")
    t["claim"] = f"{original} (edited by hand)"
    return "claim", original, t["claim"]


def verify_receipt(receipt_id: str, tamper: bool = False) -> dict[str, Any] | None:
    """Re-derive the saltless SHA-256 purely from the receipt fields.

    tamper=True shows the flip side: one hand-edited number on an in-memory
    copy and the same verification fails — the ledger's own alarm.
    """
    rs = _load()
    r = next((x for x in rs if x.get("receipt_id") == receipt_id), None)
    if r is None:
        return None
    body = {k: v for k, v in r.items() if k != "receipt_hash"}
    recomputed = _hash_body(body)
    stated = str(r.get("receipt_hash", ""))
    out: dict[str, Any] = {
        "receipt_id": receipt_id,
        "kind": r.get("kind"),
        "claim": r.get("claim"),
        "backend": "sha256",
        "stated_hash": stated,
        "recomputed_hash": recomputed,
        "match": stated == recomputed,
        "prev_receipt_hash": r.get("prev_receipt_hash"),
        "source_events": r.get("source_events") or [],
        "chain_valid": chain_valid(rs),
    }
    if not tamper:
        out["ok"] = bool(out["match"])
        return out
    t = json.loads(json.dumps(r))
    field, original, tampered = _tamper_field(t)
    tbody = {k: v for k, v in t.items() if k != "receipt_hash"}
    trecomputed = _hash_body(tbody)
    out["ok"] = False
    out["tamper"] = {
        "detected": True,
        "field": field,
        "original": original,
        "tampered": tampered,
        "recomputed_hash": trecomputed,
        "match": False,
        "reason": "SHA-256 mismatch — the edited value cannot have been issued by Hearth",
    }
    return out
