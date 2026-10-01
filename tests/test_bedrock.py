from unittest.mock import MagicMock, patch
import os
from hearth import brains


def test_bedrock_converse_schema_and_system_separation():
    mock_boto = MagicMock()
    mock_client = MagicMock()
    mock_boto.client.return_value = mock_client
    
    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": "Bedrock reasoning complete."}]}},
        "usage": {"inputTokens": 120, "outputTokens": 45, "totalTokens": 165},
        "metrics": {"latencyMs": 412.5}
    }
    
    messages = [
        {"role": "system", "content": "You are a secure operations agent."},
        {"role": "user", "content": "Turn down living room thermostat."}
    ]
    
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_REGION": "us-east-1", "AWS_BEDROCK_MODEL": "claude-sonnet"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": MagicMock()}):
        
        res = brains._call_bedrock(messages, max_tokens=600)
        
        assert res is not None
        assert res.provider == "aws-bedrock"
        assert res.tokens_used == 165
        assert res.text == "Bedrock reasoning complete."
        assert res.latency_ms == 412.5
        assert res.model == "us.anthropic.claude-3-5-sonnet-20241022-v2:0"
        
        call_kwargs = mock_client.converse.call_args[1]
        assert "system" in call_kwargs
        assert call_kwargs["system"] == [{"text": "You are a secure operations agent."}]
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"


def test_bedrock_nova_pro_model_routing():
    mock_boto = MagicMock()
    mock_client = MagicMock()
    mock_boto.client.return_value = mock_client
    
    mock_client.converse.return_value = {
        "output": {"message": {"content": [{"text": "Nova Pro execution."}]}},
        "usage": {"inputTokens": 80, "outputTokens": 20, "totalTokens": 100},
        "metrics": {"latencyMs": 195.0}
    }
    
    messages = [{"role": "user", "content": "What is the solar status?"}]
    
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1", "AWS_REGION": "us-east-1", "AWS_BEDROCK_MODEL": "nova-pro"}), \
         patch.dict("sys.modules", {"boto3": mock_boto, "botocore.config": MagicMock()}):
        
        res = brains._call_bedrock(messages, max_tokens=300)
        
        assert res is not None
        assert res.provider == "aws-bedrock"
        assert res.model == "us.amazon.nova-pro-v1:0"
        assert res.tokens_used == 100


def test_bedrock_fallback_on_import_error():
    messages = [{"role": "user", "content": "hello"}]
    with patch.dict(os.environ, {"AWS_BEDROCK_ENABLED": "1"}), \
         patch.dict("sys.modules", {"boto3": None}):
        res = brains._call_bedrock(messages, max_tokens=200)
        assert res is not None
        assert res.fallback is True
        assert res.provider == "aws-bedrock-simulated"
