"""Vault: secrets never reach the model. {{vault:NAME}} placeholders + redaction."""
from __future__ import annotations
import os
import re

PLACEHOLDER_RE = re.compile(r"\{\{vault:([A-Za-z0-9_]+)\}\}")
SECRET_HINTS = ("sk-", "key", "token", "secret", "code", "otp", "password")


def resolve(text: str) -> str:
    """Replace {{vault:NAME}} with env value. Missing -> empty (fail-closed for secrets)."""
    def _sub(m: re.Match) -> str:
        return os.environ.get(f"VAULT_{m.group(1)}", os.environ.get(m.group(1), ""))
    return PLACEHOLDER_RE.sub(_sub, text)


def redact(text: str) -> str:
    """Redact likely secrets + one-time codes before model sees output."""
    red = PLACEHOLDER_RE.sub("•••", text)
    # 4-8 digit OTP-ish codes
    red = re.sub(r"\b\d{4,8}\b", "•••", red)
    for hint in ("api_key", "apikey", "Authorization", "Bearer"):
        red = red.replace(hint, "[redacted]")
    # Bearer tokens
    red = re.sub(r"Bearer\s+[A-Za-z0-9\-._~+/=]+", "Bearer •••", red)
    # Long hex blobs (sk-...)
    red = re.sub(r"sk-[A-Za-z0-9\-_]{8,}", "sk-•••", red)
    return red
