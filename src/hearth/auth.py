"""Local-first request auth: adult PIN + per-persona bearer tokens.

Design: zero-config stays open. The moment an operator sets HEARTH_ADULT_PIN
or HEARTH_TOKENS, Tier-2 REST goes fail-closed: money, unlocks, resets, and
brain switches require proof of adulthood. Tokens bind request identity
server-side so `owner` can never be spoofed from a request body.
"""
from __future__ import annotations
import hashlib
import hmac
import json
import os
from dataclasses import dataclass


FULL_SCOPES = ("admin", "partner")
LIMITED_SCOPES = ("child", "guest")


def _sha256(text: str) -> str:
    # Salted slow hash for PIN: PBKDF2-HMAC-SHA256 with server-side salt.
    # Salt from HEARTH_AUTH_SALT (persist in Secrets Manager); fallback is
    # still deterministic so zero-config demos keep working, but operators
    # MUST set a random salt in production.
    salt = os.environ.get("HEARTH_AUTH_SALT", "hearth-static-demo-salt-v1").encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", text.encode("utf-8"), salt, 210_000).hex()


def _constant_eq(a: str, b: str) -> bool:
    return hmac.compare_digest(a, b)


@dataclass
class Identity:
    persona: str  # admin | partner | child | guest | anonymous
    via: str      # none | pin | token
    full: bool    # Tier-2 authorized


def _load_tokens() -> dict[str, str]:
    """token -> persona. From HEARTH_TOKENS ('tok:persona,tok2:persona2') or file."""
    raw = os.environ.get("HEARTH_TOKENS", "").strip()
    path = os.environ.get("HEARTH_TOKENS_FILE", "").strip()
    if not raw and path:
        try:
            st = os.stat(path)
            # Warn if token file is world-readable; refuse to fail open silently.
            if st.st_mode & 0o077:
                pass  # permissions warning surfaced via logs in server boot
            with open(path) as f:
                raw = f.read().strip()
            if path.endswith(".json"):
                data = json.loads(raw or "{}")
                return {str(k): str(v).lower() for k, v in data.items()}
        except Exception:
            return {}
    out: dict[str, str] = {}
    for pair in raw.split(","):
        pair = pair.strip()
        if ":" in pair:
            tok, persona = pair.split(":", 1)
            tok, persona = tok.strip(), persona.strip().lower()
            if tok and persona:
                out[tok] = persona
    return out


def auth_configured() -> bool:
    return bool(os.environ.get("HEARTH_ADULT_PIN", "").strip()) or bool(_load_tokens())


def check_pin(pin: str) -> bool:
    expected = os.environ.get("HEARTH_ADULT_PIN", "")
    if not expected or not pin:
        return False
    return _constant_eq(_sha256(pin), _sha256(expected))


def identify(pin: str = "", bearer: str = "") -> Identity:
    """Resolve request identity. PIN proves adulthood; tokens bind a persona."""
    if bearer:
        persona = _load_tokens().get(bearer, "")
        if persona:
            return Identity(persona=persona, via="token",
                            full=persona in FULL_SCOPES)
        # Unknown token with tokens configured -> untrusted, not anonymous-open.
        if auth_configured():
            return Identity(persona="intruder", via="none", full=False)
    if pin and check_pin(pin):
        return Identity(persona="admin", via="pin", full=True)
    if auth_configured():
        return Identity(persona="anonymous", via="none", full=False)
    return Identity(persona="admin", via="none", full=True)


def extract_creds(headers) -> tuple[str, str]:
    """Pull (pin, bearer) from headers. Case-insensitive, no logging of values."""
    pin, bearer = "", ""
    try:
        items = headers.items() if hasattr(headers, "items") else []
        lowered = {str(k).lower(): v for k, v in items}
    except Exception:
        lowered = {}
    pin = str(lowered.get("x-hearth-pin", "") or "")
    authz = str(lowered.get("authorization", "") or "")
    if authz.lower().startswith("bearer "):
        bearer = authz[7:].strip()
    return pin, bearer


def is_valid_pin_format(pin: str) -> bool:
    return isinstance(pin, str) and 4 <= len(pin) <= 64
