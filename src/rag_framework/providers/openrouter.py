"""OpenRouter chat-completions gateway with structured JSON output."""

import json
from dataclasses import asdict
from time import perf_counter
from typing import Any, Callable
from urllib.request import Request, urlopen

from rag_framework.config import Settings
from rag_framework.registry.model_registry import ResolvedModel


class OpenRouterGateway:
    def __init__(self, settings: Settings, request_call: Callable[..., Any] | None = None) -> None:
        self.settings = settings
        self.request_call = request_call or urlopen

    def complete(self, model: ResolvedModel, messages: list[dict[str, str]], *, request_id: str | None = None) -> dict[str, Any]:
        if not self.settings.openrouter_api_key:
            raise RuntimeError("OPENROUTER_API_KEY is required for OpenRouter execution")
        payload = json.dumps({"model": model.model, "messages": messages, "response_format": {"type": "json_object"}}).encode("utf-8")
        request = Request(
            f"{self.settings.openrouter_base_url.rstrip('/')}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.settings.openrouter_api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/OptimusPrime2710/RAG-final-assignment",
                "X-Title": "Multi-Agent RAG Framework",
            },
            method="POST",
        )
        started = perf_counter()
        response = self.request_call(request, timeout=60)
        body = json.loads(response.read().decode("utf-8"))
        content = body["choices"][0]["message"]["content"]
        result = json.loads(content) if isinstance(content, str) else content
        usage = body.get("usage", {})
        result["_model_execution"] = {
            **asdict(model),
            "purpose": "agent_execution",
            "request_id": request_id,
            "latency_ms": round((perf_counter() - started) * 1000, 2),
            "usage": usage,
        }
        return result

    def execute_request(self, model: ResolvedModel, request: Any) -> dict[str, Any]:
        """Adapt an ExecutorRequest to the gateway callable expected by agents."""
        messages = [
            {"role": "system", "content": "Return only a JSON object matching the requested task output."},
            {"role": "user", "content": json.dumps({"task": request.task, "inputs": request.inputs, "previous_failure": request.previous_failure})},
        ]
        return self.complete(model, messages, request_id=request.request_id)
