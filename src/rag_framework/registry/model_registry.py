"""Configuration-driven model resolution."""

from dataclasses import dataclass

from rag_framework.config import Settings


@dataclass(frozen=True)
class ResolvedModel:
    provider: str
    model: str
    size: str


class ModelRegistry:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    def resolve(self, size: str) -> ResolvedModel:
        if size == "small":
            model = self.settings.llm_small_model
        elif size == "medium":
            model = self.settings.llm_medium_model
        else:
            raise ValueError(f"unsupported model size: {size}")
        if not model:
            raise RuntimeError(f"no OpenRouter model configured for {size}")
        return ResolvedModel(provider="openrouter", model=model, size=size)
