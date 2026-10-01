import os, tempfile
os.environ["HEARTH_STATE_DIR"] = tempfile.mkdtemp()

from hearth import planner, planner_dag
from hearth import home_mock


def test_b1_dag_decomposes():
    spec = planner_dag.decompose_goal("design cozy living room lighting")
    tools = [n["tool"] for n in spec["nodes"]]
    assert "home_get_state" in tools
    assert "mcp_app_lighting_designer" in tools
    assert len(spec["nodes"]) >= 2
    assert all("depends_on" in n for n in spec["nodes"])
    assert len(spec["edges"]) >= 1


def test_b1_state_persists_across_sessions():
    s1 = planner.orchestrate_dag("restock pantry coffee", session_id="b1test123")
    assert s1["session_id"] == "b1test123"
    assert s1["media_card"]["type"] == "media-card"
    assert "carousel" in s1["media_card"] and "purchase_action" in s1["media_card"]
    # Resume same session id with a follow-up goal: history retained
    s2 = planner.orchestrate_dag("restock pantry coffee again", session_id="b1test123")
    assert s2["session_id"] == "b1test123"
    got = planner.dag_get_session("b1test123")
    assert got["ok"] is True
    assert got["session"]["session_id"] == "b1test123"
    assert "history" in got["session"]
    listed = planner.dag_list_sessions()
    assert listed["ok"] is True and listed["count"] >= 1


def test_b1_gated_action_returns_approval_required():
    home_mock.toggle_lock(door="front_door", locked=True)
    out = planner.orchestrate_dag("please unlock the front door now")
    assert out.get("approval_required") is True
    statuses = {n["status"] for n in out["dag"]}
    assert "awaiting_approval" in statuses
    # Door stays locked: propose-never-execute
    assert home_mock.get_state()["entryway"]["lock"]["front_door"] == "locked"


def test_b1_media_cards_shape():
    for kind, title in [("lighting_designer", "Lighting Designer"),
                        ("subscription_roi", "Subscription ROI"),
                        ("pantry_restock", "Pantry Restock")]:
        card = planner.media_card(kind)
        assert card["type"] == "media-card"
        assert card["title"] == title
        assert isinstance(card["carousel"]["items"], list) and len(card["carousel"]["items"]) > 0
    pantry = planner.media_card("pantry_restock")
    assert pantry["purchase_action"]["gated"] is True
    assert pantry["purchase_action"]["tool"] == "actions_propose"
