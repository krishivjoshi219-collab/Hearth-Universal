"""Web UI <-> REST API field contract tests.

The frontend reads fields by name (`data.fairness_index_out_of_10`,
`c.concession_granted`, `data.audit_proof`, ...). Nothing in the type system ties
those strings to the handlers that produce them, so a renamed field renders as
`undefined` in the UI while every backend test still passes.

These tests assert the specific field names the JS depends on. Three real
mismatches were found this way:
  * the treaty dialog read `c.covenant` (API returns `concession_granted`)
  * both forensics Merkle-proof lines read `data.audit_proof_sha256`
    (API returns `audit_proof`)
  * the meta-skill toast read `data.skill.name` (API returns flat keys)
"""
import os
import re
import sys

import pytest
from starlette.testclient import TestClient

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, os.path.join(ROOT, "src"))
sys.path.insert(0, os.path.join(ROOT, "mcp-server"))

import server  # noqa: E402


@pytest.fixture(scope="module")
def client():
    return TestClient(server.mcp.streamable_http_app())


def _app_js() -> str:
    with open(os.path.join(ROOT, "web2", "js", "app.js"), encoding="utf-8") as fh:
        return fh.read()


# Endpoint -> fields app.js dereferences from the parsed response body.
UI_CONTRACTS = {
    "POST /api/mediation/treaty": (
        "POST",
        "/api/mediation/treaty",
        ["covenants", "staged_proposal_id", "fairness_index_out_of_10",
         "nash_achievement", "cooperation_coverage_pct", "envy_gap",
         "domains_conceded", "feasible_vectors_explored", "concession_budget",
         "scenario"],
    ),
    "POST /api/forensics/reconstruct": (
        "POST",
        "/api/forensics/reconstruct",
        ["verdict", "confidence_score", "summary", "timeline", "audit_proof"],
    ),
    "GET /api/swarm/grid": (
        "GET",
        "/api/swarm/grid",
        ["cooperative_rate_kwh", "economic_impact", "nodes", "voice_summary"],
    ),
    "POST /api/parliament/deliberate": (
        "POST",
        "/api/parliament/deliberate",
        ["nash_equilibrium_score", "pareto_compromise", "speeches", "vote",
         "staged_proposal_id"],
    ),
    "POST /api/causal/simulate": (
        "POST",
        "/api/causal/simulate",
        ["vulnerabilities", "grid_resilience_score", "expected_savings_usd",
         "staged_proposal_id"],
    ),
    "GET /api/acoustic/scan": (
        "GET",
        "/api/acoustic/scan",
        ["appliances", "spectral_bins", "staged_proposal_id", "voice_summary"],
    ),
    "POST /api/meta-skills/synthesize": (
        "POST",
        "/api/meta-skills/synthesize",
        ["ok", "name", "skill_id", "safety_audit", "intent", "savings_formula"],
    ),
}

META_SKILL_BODY = {"requirement": "pre-cool the living room when solar exceeds 3kW"}


@pytest.mark.parametrize("label", sorted(UI_CONTRACTS))
def test_ui_reads_only_fields_the_api_returns(client, label):
    method, path, fields = UI_CONTRACTS[label]
    if method == "POST":
        resp = client.post(path, json=META_SKILL_BODY if "meta-skills" in path else {})
    else:
        resp = client.get(path)

    assert resp.status_code == 200, f"{label} returned {resp.status_code}"
    body = resp.json()
    missing = [f for f in fields if f not in body]
    assert not missing, (
        f"{label} response is missing field(s) {missing} that web2/js/app.js reads. "
        f"Either restore the field or update the UI."
    )


def test_treaty_covenants_expose_every_field_the_dialog_renders(client):
    """The treaty dialog renders each covenant's resident, domain, percentage,
    granted text, reciprocal obligation, weight and concession level."""
    resp = client.post("/api/mediation/treaty", json={})
    assert resp.status_code == 200
    covenants = resp.json()["covenants"]
    assert covenants, "expected at least one covenant"
    for cov in covenants:
        for field in ("resident", "domain", "satisfaction_pct", "concession_granted",
                      "reciprocal_obligation", "domain_weight", "concession_level"):
            assert field in cov, f"covenant is missing '{field}'"
        # The dialog reads satisfaction_pct and formats it with a '%' suffix.
        assert isinstance(cov["satisfaction_pct"], (int, float))


def test_app_js_no_longer_references_retired_field_names():
    """Regression guard for the three mismatches this suite was written for."""
    js = _app_js()
    # Word-boundary match: a bare substring test would flag "c.covenant" inside
    # the legitimate "c.covenants" array access.
    for retired in ("c\\.covenant\\b(?!s)", "audit_proof_sha256", "data\\.skill\\.name"):
        assert not re.search(retired, js), (
            f"web2/js/app.js still reads '{retired}', which the API does not return. "
            f"It would render 'undefined' in the UI."
        )


def test_replay_endpoint_is_reachable_with_the_method_the_ui_uses(client):
    """app.js fetches /api/audit/replay?id=... with GET; assert that works."""
    from hearth import proposals

    staged = proposals.propose(kind="contract_probe", title="Contract probe", reasons="test")
    resp = client.get(f"/api/audit/replay?id={staged['id']}")
    assert resp.status_code == 200
    body = resp.json()
    for field in ("why", "execution", "audit_trail", "chain_valid", "undo_available"):
        assert field in body, f"replay response is missing '{field}'"


def test_every_data_field_app_js_reads_is_a_known_identifier(client):
    """Broad sweep: flag any `data.<field>` access that no endpoint returns.

    Guards against new UI code referencing a field that does not exist yet.
    """
    js = _app_js()
    fields = sorted(set(re.findall(r"\bdata\.([a-z_][a-z0-9_]*)", js)))

    # Fields legitimately produced by /api/chat, /api/decide, /api/undo and the
    # other endpoints not covered by UI_CONTRACTS above.
    known_elsewhere = {
        "active_model", "audit_trail", "blocked", "causal_confidence", "chain_valid",
        "dag", "diagnostics", "discovered_models", "draft", "economic_arbitrage",
        "error", "event", "execution", "intent", "kind", "local_clearing_price_usd_kwh",
        "message", "note", "ok", "reason", "replay_note", "skill", "speeches", "summary",
        "text", "timeline_events", "title", "undo_available",
        "utility_sell_rate_usd_kwh", "vote", "why",
    }
    returned = set()
    for method, path, _fields in UI_CONTRACTS.values():
        resp = client.post(path, json=META_SKILL_BODY if "meta-skills" in path else {}) \
            if method == "POST" else client.get(path)
        if resp.status_code == 200:
            returned.update(resp.json().keys())

    unexplained = [f for f in fields
                   if f not in returned and f not in known_elsewhere
                   and f not in ("concession_budget", "cooperation_coverage_pct",
                                 "domains_conceded", "envy_gap", "nash_achievement",
                                 "feasible_vectors_explored", "scenario",
                                 "synthesis", "vulnerabilities")]
    assert not unexplained, (
        f"app.js reads data.{unexplained} which no endpoint appears to return. "
        f"Verify each is produced by its handler, or remove the access."
    )