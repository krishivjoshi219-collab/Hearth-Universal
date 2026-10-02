"""Vault: secrets never reach the model. {{vault:NAME}} placeholders + redaction."""
from __future__ import annotations
import os
import re

PLACEHOLDER_RE = re.compile(r"\{\{vault:([A-Za-z0-9_]+)\}\}")
SECRET_HINTS = ("sk-", "key", "token", "secret", "code", "otp", "password")


def set_secret(name: str, value: str) -> None:
    """Store a secret for this process (env-backed). Used by custom provider registration."""
    name = str(name or "").strip()
    if not name or not re.fullmatch(r"[A-Za-z0-9_]{1,64}", name):
        raise ValueError("invalid secret name")
    os.environ[f"VAULT_{name}"] = str(value or "")


def resolve(text: str) -> str:
    """Replace {{vault:NAME}} with env value. Missing -> empty (fail-closed for secrets)."""
    def _sub(m: re.Match) -> str:
        return os.environ.get(f"VAULT_{m.group(1)}", os.environ.get(m.group(1), ""))
    return PLACEHOLDER_RE.sub(_sub, text)


def redact(text: str) -> str:
    """Redact likely secrets + one-time codes before model sees output."""
    if not isinstance(text, str):
        try:
            text = str(text)
        except Exception:
            return "•••"
    red = PLACEHOLDER_RE.sub("•••", text)
    # AWS / GitHub / Slack / generic private keys
    red = re.sub(r"AKIA[0-9A-Z]{12,}", "AKIA•••", red)
    red = re.sub(r"aws_secret_access_key\s*[:=]\s*\S+", "aws_secret_access_key •••", red, flags=re.I)
    red = re.sub(r"gh[pousr]_[A-Za-z0-9]{8,}", "gh•••", red)
    red = re.sub(r"xox[bpars]-[A-Za-z0-9\-]{8,}", "xox•••", red)
    red = re.sub(r"-----BEGIN [A-Z ]*PRIVATE KEY-----[\s\S]{0,200}?-----END", "•••PRIVATE KEY•••", red)
    # 4-8 digit OTP-ish codes
    red = re.sub(r"\b\d{4,8}\b", "•••", red)
    for hint in ("api_key", "apikey", "Authorization", "Bearer", "client_secret", "refresh_token"):
        red = red.replace(hint, "[redacted]")
    # Bearer tokens
    red = re.sub(r"Bearer\s+[A-Za-z0-9\-._~+/=]+", "Bearer •••", red)
    # Long hex blobs (sk-...)
    red = re.sub(r"sk-[A-Za-z0-9\-_]{8,}", "sk-•••", red)
    return red
