"""Over-the-wire smoke proof: real JSON-RPC against a live server process.
Run: pytest tests/test_mcp_http.py  (spins server on :8799, kills it after)
"""
import json
import os
import subprocess
import tempfile
import time
import urllib.request

PORT = 8799
BASE = f"http://localhost:{PORT}"
ROOT = os.path.join(os.path.dirname(__file__), "..")


def _rpc(method, params=None, rid=1):
    body = json.dumps({"jsonrpc": "2.0", "id": rid, "method": method, "params": params or {}}).encode()
    req = urllib.request.Request(
        BASE + "/mcp", data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())


def _wait_healthy(proc, timeout=40):
    start = time.time()
    while time.time() - start < timeout:
        try:
            with urllib.request.urlopen(BASE + "/health", timeout=5) as r:
                if json.loads(r.read().decode()).get("status") == "ok":
                    return
        except Exception:
            pass
        if proc.poll() is not None:
            raise RuntimeError("server exited during startup")
        time.sleep(0.05)
    raise RuntimeError("server did not become healthy")


def test_mcp_http_smoke():
    env = dict(os.environ, PORT=str(PORT), HEARTH_STATE_DIR=tempfile.mkdtemp(), PYTHONPATH="src")
    proc = subprocess.Popen(["python3", "mcp-server/server.py"], cwd=ROOT, env=env,
                            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        _wait_healthy(proc)
        init = _rpc("initialize", {"protocolVersion": "2025-11-25", "capabilities": {},
                                   "clientInfo": {"name": "smoke", "version": "0"}})
        assert init["result"]["protocolVersion"] == "2025-11-25"
        tools = _rpc("tools/list", {}, rid=2)["result"]["tools"]
        names = {t["name"] for t in tools}
        assert {"planner_orchestrate", "home_toggle_lock", "actions_decide", "audit_verify"} <= names
        scan = _rpc("tools/call", {"name": "inbox_scan", "arguments": {}}, rid=3)
        assert scan["result"]["isError"] is False
        # Unlock over bare MCP must NOT execute — approval_required instead.
        gated = _rpc("tools/call", {"name": "home_toggle_lock",
                                    "arguments": {"door": "front_door", "locked": False}}, rid=4)
        assert gated["result"]["isError"] is False
        assert "approval_required" in json.dumps(gated["result"])
        # Unknown method surfaces a JSON-RPC error, not a crash.
        err = _rpc("nope/not_a_method", {}, rid=5)
        assert "error" in err
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=2)
        except subprocess.TimeoutExpired:
            proc.kill()
