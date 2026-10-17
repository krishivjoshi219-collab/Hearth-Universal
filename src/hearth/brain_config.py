"""Bring-your-own-key brain configuration (persisted, masked, pre-flighted).

The Hearth preview lets a household connect its *own* AI so free-form
questions get real answers — OpenAI, OpenRouter, Groq, a local Ollama or any
OpenAI-compatible endpoint, or Amazon Bedrock. This module owns that setting:

  * Storage:  ``state/brain_config.json`` (chmod 0600, crash-safe atomic write)
  * Apply:    written into the process env exactly where ``brains.chat``
              already looks (``HEARTH_BRAIN_PROVIDER`` / ``HEARTH_BASE_URL`` /
              ``HEARTH_MODEL`` / ``VAULT_MODEL_KEY`` / ``AWS_*``).
  * Privacy:  the key is never echoed back. ``status()`` only ever exposes a
              masked hint (last 4 characters), and nothing logs the raw value.

The persisted file is deliberately *not* loaded at import time: the server
calls :func:`load` on startup, while the test suite imports the server without
picking up (or clobbering) a developer's real key.

Fail-safe posture: everything degrades to the offline local engine, so a bad
key or dead endpoint can never crash a request — it just answers locally with
an honest notice (see ``brains.chat``).
"""
from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

from . import atomic

MAX_KEY_LEN = 512
MAX_URL_LEN = 300
MAX_MODEL_LEN = 120

# Presets are server-owned so the preview and the API agree on ids and
# defaults. Users can edit endpoint/model before saving; "custom" starts blank.
PRESETS: list[dict[str, Any]] = [
    {
        "id": "openai",
        "name": "OpenAI",
        "kind": "openai-compatible",
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "key_required": True,
        "key_hint": "sk-…",
        "note": "Your key is billed by OpenAI directly.",
    },
    {
        "id": "groq",
        "name": "Groq Cloud",
        "kind": "openai-compatible",
        "base_url": "https://api.groq.com/openai/v1",
        "model": "llama-3.3-70b-versatile",
        "key_required": True,
        "key_hint": "gsk_…",
        "note": "Very fast open models.",
    },
    {
        "id": "openrouter",
        "name": "OpenRouter",
        "kind": "openai-compatible",
        "base_url": "https://openrouter.ai/api/v1",
        "model": "openai/gpt-4o-mini",
        "key_required": True,
        "key_hint": "sk-or-…",
        "note": "One key, hundreds of models.",
    },
    {
        "id": "ollama",
        "name": "Ollama (on this machine)",
        "kind": "openai-compatible",
        "base_url": "http://127.0.0.1:11434/v1",
        "model": "llama3.2",
        "key_required": False,
        "key_hint": "not needed",
        "note": "Fully local; nothing leaves the house.",
    },
    {
        "id": "custom",
        "name": "Custom / self-hosted",
        "kind": "openai-compatible",
        "base_url": "",
        "model": "",
        "key_required": False,
        "key_hint": "optional",
        "note": "Any OpenAI-compatible endpoint: vLLM, LM Studio, a gateway…",
    },
    {
        "id": "bedrock",
        "name": "Amazon Bedrock",
        "kind": "bedrock",
        "base_url": "",
        "model": "us.amazon.nova-pro-v1:0",
        "key_required": False,
        "key_hint": "AWS credentials",
        "note": "Uses your AWS credentials and region.",
    },
]

_PRESET_INDEX = {p["id"]: p for p in PRESETS}
_HOST_RE = re.compile(r"^[A-Za-z0-9.\-]+$")
_REGION_RE = re.compile(r"^[a-z]{2}(-gov)?-[a-z]+-\d$")


def _state_dir() -> Path:
    d = Path(os.environ.get("HEARTH_STATE_DIR", "state"))
    d.mkdir(parents=True, exist_ok=True)
    return d


def config_file() -> Path:
    return _state_dir() / "brain_config.json"


def presets() -> list[dict[str, Any]]:
    return [dict(p) for p in PRESETS]


# --------------------------------------------------------------------- apply

_ENV_FOR_PROVIDER = (
    "HEARTH_BRAIN_PROVIDER",
    "HEARTH_BASE_URL",
    "HEARTH_MODEL",
    "VAULT_MODEL_KEY",
    "AWS_BEDROCK_ENABLED",
    "AWS_BEDROCK_MODEL",
    "AWS_DEFAULT_REGION",
)


def _apply(cfg: dict[str, Any]) -> None:
    """Write a validated config into the env where brains.chat reads it."""
    provider = cfg["provider"]
    if provider == "bedrock":
        os.environ["HEARTH_BRAIN_PROVIDER"] = "bedrock"
        os.environ["AWS_BEDROCK_ENABLED"] = "1"
        os.environ["AWS_BEDROCK_MODEL"] = cfg["model"]
        os.environ["HEARTH_MODEL"] = cfg["model"]
        if cfg.get("region"):
            os.environ["AWS_DEFAULT_REGION"] = cfg["region"]
        if cfg.get("access_key_id"):
            os.environ["AWS_ACCESS_KEY_ID"] = cfg["access_key_id"]
        if cfg.get("secret_access_key"):
            os.environ["AWS_SECRET_ACCESS_KEY"] = cfg["secret_access_key"]
        return

    os.environ["HEARTH_BRAIN_PROVIDER"] = provider
    os.environ["HEARTH_BASE_URL"] = cfg["base_url"]
    os.environ["HEARTH_MODEL"] = cfg["model"]
    # Ollama ignores Authorization but brains.chat refuses empty-key requests;
    # a non-secret placeholder keeps the local path live without a real key.
    if cfg.get("api_key"):
        os.environ["VAULT_MODEL_KEY"] = cfg["api_key"]
    elif provider == "ollama":
        os.environ["VAULT_MODEL_KEY"] = "ollama-local"
    else:
        os.environ.pop("VAULT_MODEL_KEY", None)


def _unapply() -> None:
    for k in _ENV_FOR_PROVIDER:
        os.environ.pop(k, None)
    os.environ["AWS_BEDROCK_ENABLED"] = "0"


# -------------------------------------------------------------------- status

def _read_file() -> dict[str, Any] | None:
    f = config_file()
    try:
        if not f.exists():
            return None
        data = json.loads(f.read_text())
        return data if isinstance(data, dict) else None
    except Exception:
        return None


def status() -> dict[str, Any]:
    """Redacted status for the preview. Never contains the raw key."""
    cfg = _read_file()
    base_url = ""
    if cfg:
        base_url = str(cfg.get("base_url") or "")
        provider = str(cfg.get("provider") or "")
    else:
        provider = os.environ.get("HEARTH_BRAIN_PROVIDER", "local")
        base_url = os.environ.get("HEARTH_BASE_URL", "")

    preset = _PRESET_INDEX.get(provider, {})
    env_key = os.environ.get("OPENAI_API_KEY", "")

    host = ""
    m = re.match(r"^https?://([^/:]+)", base_url)
    if m:
        host = m.group(1)

    if cfg:
        configured = True
        model = str(cfg.get("model") or "")
        since = cfg.get("saved_at")
        key = str(cfg.get("api_key") or "")
    else:
        # Env-provided config (docker/AWS deployments) still counts as connected.
        key = os.environ.get("VAULT_MODEL_KEY", "") or env_key
        configured = bool(provider and provider not in ("local", "") and (key or provider == "ollama"))
        model = os.environ.get("HEARTH_MODEL", "")
        since = None

    # Masked hint only when something is actually connected; a stray key in the
    # shell environment must never leak four characters on a disconnected box.
    key_hint = ""
    if configured and len(key) >= 8:
        key_hint = "…" + key[-4:]

    return {
        "ok": True,
        "configured": configured,
        "provider": provider or "local",
        "provider_name": preset.get("name") or ("Local engine" if provider == "local" else provider),
        "kind": preset.get("kind", "openai-compatible"),
        "model": model,
        "base_url": base_url,
        "host": host,
        "key_hint": key_hint,
        "source": "file" if cfg else ("env" if configured else "none"),
        "since": since,
        "env_key_available": bool(env_key),
        "presets": presets(),
    }


# --------------------------------------------------------------------- save

def _clean_str(v: Any, limit: int) -> str:
    s = str(v or "").strip()
    if any(ch in s for ch in ("\n", "\r", "\x00")):
        raise ValueError("invalid characters")
    return s[:limit]


def save(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate + persist + apply. Raises ValueError with a friendly message."""
    if not isinstance(payload, dict):
        raise ValueError("settings object required")
    provider = _clean_str(payload.get("provider"), 40).lower()
    if provider not in _PRESET_INDEX:
        raise ValueError("Unknown provider. Pick one of: " + ", ".join(p["id"] for p in PRESETS))
    preset = _PRESET_INDEX[provider]

    model = _clean_str(payload.get("model"), MAX_MODEL_LEN) or str(preset["model"])
    api_key = _clean_str(payload.get("api_key"), MAX_KEY_LEN)
    base_url = _clean_str(payload.get("base_url"), MAX_URL_LEN) or str(preset["base_url"])

    cfg: dict[str, Any] = {"provider": provider, "model": model, "saved_at": time.time()}

    if provider == "bedrock":
        region = _clean_str(payload.get("region"), 40) or os.environ.get("AWS_DEFAULT_REGION", "us-east-1")
        if not _REGION_RE.match(region):
            raise ValueError("Region should look like us-east-1")
        cfg["base_url"] = ""
        cfg["region"] = region
        cfg["access_key_id"] = _clean_str(payload.get("access_key_id"), MAX_KEY_LEN)
        cfg["secret_access_key"] = _clean_str(payload.get("secret_access_key"), MAX_KEY_LEN)
        if not cfg["access_key_id"] and not os.environ.get("AWS_ACCESS_KEY_ID"):
            raise ValueError("AWS access key id is required for Bedrock")
    else:
        if not base_url:
            raise ValueError("Endpoint URL is required")
        m = re.match(r"^https?://([^/:]+)/?", base_url)
        if not m or not _HOST_RE.match(m.group(1)):
            raise ValueError("Endpoint must be a full http(s):// URL")
        using_env_key = bool(os.environ.get("OPENAI_API_KEY"))
        if preset.get("key_required") and not api_key and not (provider == "openai" and using_env_key):
            raise ValueError("An API key is required for " + str(preset["name"]))
        if not model:
            raise ValueError("Model name is required")
        cfg["base_url"] = base_url
        if api_key:
            cfg["api_key"] = api_key

    f = config_file()
    with atomic.locked(f):
        atomic.atomic_write_text(f, json.dumps(cfg, indent=2))
        os.chmod(f, 0o600)
    _apply(cfg)
    out = status()
    out["message"] = "Connected. Free-form questions now run on your own AI."
    return out


def clear() -> dict[str, Any]:
    """Disconnect: remove the persisted config and drop the env overlay."""
    f = config_file()
    try:
        with atomic.locked(f):
            if f.exists():
                f.unlink()
    except Exception:
        try:
            f.unlink(missing_ok=True)
        except Exception:
            pass
    _unapply()
    out = status()
    out["message"] = "Disconnected. The built-in offline engine is still active."
    return out


def load() -> bool:
    """Apply the persisted config to this process (server startup). Idempotent."""
    cfg = _read_file()
    if not cfg:
        return False
    try:
        _apply(cfg)
        return True
    except Exception:
        return False


# ------------------------------------------------------------------- test

def test_connection(timeout: float = 6.0) -> dict[str, Any]:
    """Cheap live pre-flight against the *saved* config. Fail-safe never raises."""
    cfg = _read_file()
    if not cfg:
        return {"ok": False, "error": "Nothing connected yet."}
    provider = str(cfg.get("provider") or "")
    try:
        if provider == "bedrock":
            import importlib.util
            if importlib.util.find_spec("boto3") is None:
                return {"ok": False, "error": "boto3 is not installed"}
            has_creds = bool(
                (cfg.get("access_key_id") and cfg.get("secret_access_key"))
                or (os.environ.get("AWS_ACCESS_KEY_ID") and os.environ.get("AWS_SECRET_ACCESS_KEY"))
            )
            if not has_creds:
                return {"ok": False, "error": "AWS credentials are missing"}
            return {"ok": True, "provider": "bedrock",
                    "detail": "Credentials present. A live call happens on your first question."}

        from . import brains, vault
        base_url = str(cfg.get("base_url") or "")
        host = brains._host_of(base_url).lower()
        if brains.STRICT_EGRESS and not brains._egress_allowed(host):
            return {"ok": False, "error": f"Egress to {host} is blocked by policy"}
        key = str(cfg.get("api_key") or "")
        if not key and provider == "ollama":
            key = "ollama-local"
        if not key and provider == "openai":
            key = os.environ.get("OPENAI_API_KEY", "")
        req = urllib.request.Request(
            base_url.rstrip("/") + "/models",
            headers={"Authorization": f"Bearer {key}"} if key else {},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data = json.loads(r.read().decode())
        models = [str(m.get("id")) for m in (data.get("data") or []) if isinstance(m, dict)]
        return {
            "ok": True,
            "provider": provider,
            "models": models[:5],
            "count": len(models),
            "detail": f"Reached {host}" + (f" · {len(models)} models visible" if models else ""),
        }
    except Exception as e:
        msg = vault_redact(f"{type(e).__name__}: {str(e)[:120]}")
        return {"ok": False, "error": msg}


def vault_redact(text: str) -> str:
    try:
        from . import vault
        return vault.redact(text)
    except Exception:
        return text
