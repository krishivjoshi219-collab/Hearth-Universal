"""Unit & contract tests for the Direct Inter-Agent War Room IPC & MCP Layer."""

from __future__ import annotations

from pathlib import Path

from starlette.testclient import TestClient

from hearth import warroom


def test_warroom_send_and_inbox(tmp_path: Path, monkeypatch) -> None:
    ipc_file = tmp_path / "test_ipc.jsonl"
    disc_file = tmp_path / "test_discussion.md"
    disc_file.write_text("# Test War Room\n", encoding="utf-8")

    monkeypatch.setattr(warroom, "IPC_LOG", ipc_file)
    monkeypatch.setattr(warroom, "DISCUSSION_MD", disc_file)

    # 1. Send from gemini
    res1 = warroom.send_message(
        sender="gemini",
        message="Hey OpenCode, presentation layer update is live.",
        topic="presentation",
        metadata={"version": "1.0"},
    )
    assert res1["ok"] is True
    assert res1["delivered"] is True

    # 2. Send from opencode
    res2 = warroom.send_message(
        sender="opencode",
        message="Acknowledged, probe frames inspected.",
        topic="film",
    )
    assert res2["ok"] is True

    # 3. Read inbox
    inbox = warroom.get_messages(limit=10)
    assert len(inbox) == 2
    assert inbox[0]["sender"] == "gemini"
    assert inbox[1]["sender"] == "opencode"
    assert inbox[0]["topic"] == "presentation"

    # 4. Verify discussion.md was appended cleanly
    disc_text = disc_file.read_text(encoding="utf-8")
    assert "Gemini (PRESENTATION)" in disc_text
    assert "Opencode (FILM)" in disc_text


def test_warroom_status() -> None:
    st = warroom.get_warroom_status()
    assert st["status"] == "active"
    assert "film" in st
    assert "agents" in st
    assert "antigravity" in st["agents"]
    assert "opencode" in st["agents"]


def test_warroom_rest_endpoints(monkeypatch) -> None:
    # Test via server TestClient
    import os
    import sys
    ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if os.path.join(ROOT, "mcp-server") not in sys.path:
        sys.path.insert(0, os.path.join(ROOT, "mcp-server"))
    import server
    client = TestClient(server.mcp.streamable_http_app())

    # 1. Send via REST
    resp = client.post("/api/warroom/send", json={
        "sender": "gemini",
        "message": "REST test message",
        "topic": "test",
    })
    assert resp.status_code == 200
    data = resp.json()
    assert data["ok"] is True

    # 2. Inbox via REST
    resp_inbox = client.get("/api/warroom/inbox?limit=5")
    assert resp_inbox.status_code == 200
    inbox_data = resp_inbox.json()
    assert inbox_data["ok"] is True
    assert len(inbox_data["messages"]) > 0

    # 3. Status via REST
    resp_status = client.get("/api/warroom/status")
    assert resp_status.status_code == 200
    status_data = resp_status.json()
    assert status_data["ok"] is True
    assert status_data["status"] == "active"
