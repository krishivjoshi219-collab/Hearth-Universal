"""B4 AWS Builder upgrade tests (no live AWS calls -- moto-style mocks only)."""
import os
from unittest.mock import MagicMock, patch

from hearth import brains


def _mock_bedrock(text="ok", latency=123.4, tokens=42):
    mock_boto = MagicMock()
    mock_client = MagicMock()
    mock_boto.client.return_value = mock_client
    mock_sess = MagicMock()
    mock_sess.get_credentials.return_value = MagicMock()
    mock_boto.Session.return_value = mock_sess
    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": text}]}},
        "usage": {"inputTokens": 10, "outputTokens": 5, "totalTokens": tokens},
        "metrics": {"latencyMs": latency},
    }
    return mock_boto, mock_client


def test_b4_router_claude_vs_nova_cross_region():
    brains.clear_bedrock_metrics()
    with patch.dict(os.environ, {"AWS_BEDROCK_MODEL": "auto"}, clear=False):
        claude = brains.select_bedrock_model([{"role": "user", "content": "decompose this complex multi-step plan carefully"}])
        nova = brains.select_bedrock_model([{"role": "user", "content": "classify intent as json fast"}])
    assert claude.startswith("us.anthropic.claude-3-5-sonnet")
    assert nova == "us.amazon.nova-pro-v1:0"
    # cross-region inference-profile prefix required
    assert claude.startswith("us.") and nova.startswith("us.")
    # explicit alias wins over router
    with patch.dict(os.environ, {"AWS_BEDROCK_MODEL": "nova-pro"}):
        assert brains.select_bedrock_model([{"role": "user", "content": "deep reasoning"}]) == "us.amazon.nova-pro-v1:0"


def test_b4_adaptive_retry_config():
    brains.clear_bedrock_metrics()
    mock_boto, mock_client = _mock_bedrock()
    fake_config_calls = {}

    class FakeConfig:
        def __init__(self, **kw):
            fake_config_calls.update(kw)

    fake_cfg_mod = MagicMock()
    fake_cfg_mod.Config = FakeConfig
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_BEDROCK_MODEL": "claude-sonnet", "AWS_BEDROCK_MAX_ATTEMPTS": "5"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": fake_cfg_mod}):
        # has_aws_credentials uses boto3.Session -> truthy mock
        res = brains._call_bedrock([{"role": "user", "content": "hello"}], 100)
        assert res.provider == "aws-bedrock"
        assert fake_config_calls.get("retries", {}).get("mode") == "adaptive"
        assert fake_config_calls["retries"]["max_attempts"] == 5
        # client built for bedrock-runtime
        assert mock_boto.client.call_args[0][0] == "bedrock-runtime"


def test_b4_graceful_offline_fallback_no_flag_no_creds():
    brains.clear_bedrock_metrics()
    env = {k: v for k, v in os.environ.items() if k not in ("AWS_BEDROCK_ENABLED", "AWS_ACCESS_KEY_ID", "AWS_PROFILE")}
    with patch.dict(os.environ, env, clear=True):
        os.environ.pop("AWS_BEDROCK_ENABLED", None)
        assert brains.is_bedrock_enabled() is False
        assert brains._call_bedrock([{"role": "user", "content": "hello"}], 50) is None
        out = brains.chat([{"role": "user", "content": "hello"}], preferred_provider=None)
        assert out.provider in ("local-agent", "local-fallback", "openai-compatible")
    # no creds -> simulated fallback even when enabled (no charges, no network)
    mock_boto = MagicMock()
    mock_boto.Session.return_value.get_credentials.return_value = None
    mock_boto.client.return_value = MagicMock()
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_BEDROCK_MODEL": "nova-pro"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": MagicMock()}):
        with patch.object(brains, "has_aws_credentials", return_value=False):
            res = brains._call_bedrock([{"role": "user", "content": "hi"}], 50)
            assert res.fallback is True
            assert res.provider == "aws-bedrock-simulated"


def test_b4_metrics_shape_latencyMs():
    brains.clear_bedrock_metrics()
    mock_boto, _ = _mock_bedrock(text="m", latency=77.7, tokens=9)
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_BEDROCK_MODEL": "claude-sonnet"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": MagicMock()}):
        brains._call_bedrock([{"role": "user", "content": "deep reasoning task"}], 80)
    m = brains.get_bedrock_metrics()
    assert m["count"] >= 1
    assert "latencyMs" in m and isinstance(m["latencyMs"], list)
    assert m["latencyMs"][-1] == 77.7
    assert m["lastLatencyMs"] == 77.7
    assert m["avgLatencyMs"] >= 0
    assert m["recent"][-1]["model"].startswith("us.anthropic")


def test_b4_system_isolation_and_alternation():
    brains.clear_bedrock_metrics()
    mock_boto, mock_client = _mock_bedrock()
    msgs = [
        {"role": "system", "content": "You are secure."},
        {"role": "user", "content": "a"},
        {"role": "user", "content": "b"},
        {"role": "assistant", "content": "c"},
    ]
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_BEDROCK_MODEL": "claude-sonnet"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": MagicMock()}):
        brains._call_bedrock(msgs, 100)
    kwargs = mock_client.converse.call_args[1]
    assert kwargs["system"] == [{"text": "You are secure."}]
    roles = [m["role"] for m in kwargs["messages"]]
    assert roles[0] == "user"
    assert all(a != b for a, b in zip(roles, roles[1:]))
