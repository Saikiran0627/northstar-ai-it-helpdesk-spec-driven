import py_compile

from northstar_helpdesk.config import load_settings
from northstar_helpdesk.evaluation import run_evaluation
from northstar_helpdesk.model_client import AzureClaudeClient, get_model_client


def test_t_eval_001_reproducible_evaluation_runs():
    results, metrics = run_evaluation("knowledge_base")
    assert metrics["case_count"] == 5
    assert metrics["failed"] == 0
    assert metrics["average_score"] >= 0.7
    assert all(result.latency_ms >= 0 for result in results)


def test_t_eval_002_dashboard_payload_shape():
    results, metrics = run_evaluation("knowledge_base")
    assert "p50_latency_ms" in metrics
    assert results[0].case_id.startswith("EVAL-")
    assert isinstance(results[0].tool_calls, list)


def test_t_start_001_app_compiles():
    py_compile.compile("app.py", doraise=True)


def test_t_api_001_missing_azure_config_returns_controlled_failure(monkeypatch):
    monkeypatch.setenv("MODEL_PROVIDER", "azure")
    monkeypatch.delenv("AZURE_CLAUDE_ENDPOINT", raising=False)
    monkeypatch.delenv("AZURE_CLAUDE_API_KEY", raising=False)
    monkeypatch.delenv("AZURE_CLAUDE_MODEL", raising=False)
    settings = load_settings()
    client = get_model_client(settings)
    assert isinstance(client, AzureClaudeClient)
    response = client.generate("hello", "", [], [], [])
    assert not response.success
    assert "missing" in response.error.lower()
