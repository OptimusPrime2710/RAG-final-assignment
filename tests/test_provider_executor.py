import json
from pathlib import Path

from rag_framework.agents.executor import TaskExecutorAgent
from rag_framework.config import load_settings
from rag_framework.domain import ExecutorRequest, ModelRequirement
from rag_framework.providers.openrouter import OpenRouterGateway
from rag_framework.registry.model_registry import ModelRegistry
from rag_framework.registry.tool_registry import ToolRegistry


class FakeResponse:
    def read(self):
        return json.dumps({"choices": [{"message": {"content": '{"answer": "ok"}'}}]}).encode()


def test_gateway_plugs_into_model_required_executor(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("OPENROUTER_API_KEY", "key")
    monkeypatch.setenv("LLM_SMALL_MODEL", "provider/small")
    settings = load_settings(tmp_path / ".env")
    gateway = OpenRouterGateway(settings, request_call=lambda request, timeout: FakeResponse())
    executor = TaskExecutorAgent(ToolRegistry(), ModelRegistry(settings), gateway.execute_request)
    response = executor.execute(ExecutorRequest(
        request_id="req", plan_id="plan", goal_id="goal", task_id="task", executor_type="task_executor",
        task={"name": "answer", "description": "answer"}, model_requirement=ModelRequirement(required=True, size="small"),
    ))
    assert response.result["answer"] == "ok"
    assert response.result["_model_execution"]["model"] == "provider/small"
