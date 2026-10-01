"""Inbox / subscription ROI audit (B5 scope: commerce/subscriptions).

Thin wrapper over commerce subscription fixtures. All data is sandbox
(synthetic billing telemetry; no real bank APIs). Reads are Tier-1;
cancels/downgrades must go via actions_propose (Tier-2).
"""
from __future__ import annotations

from . import commerce as _commerce


def scan() -> dict:
    """Scan subscriptions with sandbox marking + computed ROI."""
    data = _commerce.scan_subscriptions()
    roi = _commerce.audit_subscription_roi()
    return {
        **data,
        "roi": roi,
        "sandbox": True,
        "data_source": _commerce.DATA_SOURCE,
        "note": _commerce.SANDBOX_NOTE,
    }


def audit_roi() -> dict:
    """ROI audit: $ savings calc (sandbox fixture)."""
    return _commerce.audit_subscription_roi()


def depletion_forecast() -> list[dict]:
    """Computed depletion velocity forecast (sandbox)."""
    return _commerce.get_depletion_forecast()
