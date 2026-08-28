import json
from pathlib import Path

from rag_framework.config import load_settings
from rag_framework.providers.openrouter import OpenRouterGateway
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.registry.tool_registry import ToolRegistry
from rag_framework.tools.jira_mcp import JiraMCPAdapter


class FakeResponse:
    def read(self):
        return json.dumps({"choices": [{"message": {"content": '{"answer": "ok"}'}}], "usage": {"total_tokens": 4}}).encode()


def test_openrouter_gateway_returns_json_and_usage(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("LLM_SMALL_MODEL", "provider/small")
    settings = load_settings(tmp_path / ".env")
    gateway = OpenRouterGateway(settings, request_call=lambda request, timeout: FakeResponse())
    result = gateway.complete(ModelRegistry(settings).resolve("small"), [{"role": "user", "content": "Return JSON"}], request_id="req")
    assert result["answer"] == "ok"
    assert result["_model_execution"]["usage"]["total_tokens"] == 4


def test_jira_mcp_tools_use_common_registry() -> None:
    calls = []
    adapter = JiraMCPAdapter(lambda tool, inputs: calls.append((tool, inputs)) or {"ok": True})
    registry = ToolRegistry()
    adapter.register_tools(registry, ["issue_search", "issue_create"])
    assert registry.discover("jira_issue_search")[0].type == "mcp"
    assert registry.execute("jira.issue_search", {"jql": "project = DEMO"}) == {"ok": True}
    assert calls == [("issue_search", {"jql": "project = DEMO"})]
