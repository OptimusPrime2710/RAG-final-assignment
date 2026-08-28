"""Environment-backed application settings."""

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    openrouter_api_key: str | None
    openrouter_base_url: str
    llm_small_model: str | None
    llm_medium_model: str | None
    planner_model_size: str
    executor_model_size: str
    validator_model_size: str
    orchestrator_model_size: str
    chroma_persist_directory: Path
    jira_mcp_url: str | None
    jira_api_token: str | None
    jira_email: str | None
    plans_directory: Path
    max_retry_attempts: int

    def validate_for(self, *, openrouter: bool = False, jira: bool = False) -> None:
        """Validate settings required by an explicitly enabled integration."""
        model_sizes = {
            "PLANNER_MODEL_SIZE": self.planner_model_size,
            "EXECUTOR_MODEL_SIZE": self.executor_model_size,
            "VALIDATOR_MODEL_SIZE": self.validator_model_size,
            "ORCHESTRATOR_MODEL_SIZE": self.orchestrator_model_size,
        }
        invalid = [name for name, size in model_sizes.items() if size not in {"small", "medium"}]
        if invalid:
            raise ValueError(f"unsupported model size setting(s): {', '.join(invalid)}")
        if not 1 <= self.max_retry_attempts <= 3:
            raise ValueError("MAX_RETRY_ATTEMPTS must be between 1 and 3")
        if openrouter and (not self.openrouter_api_key or not self.llm_small_model or not self.llm_medium_model):
            raise ValueError("OPENROUTER_API_KEY, LLM_SMALL_MODEL, and LLM_MEDIUM_MODEL are required")
        if jira and (not self.jira_mcp_url or not self.jira_api_token or not self.jira_email):
            raise ValueError("JIRA_MCP_URL, JIRA_EMAIL, and JIRA_API_TOKEN are required")


def load_settings(dotenv_path: str | Path | None = None) -> Settings:
    """Load settings without requiring secrets for offline execution."""
    load_dotenv(dotenv_path)
    return Settings(
        openrouter_api_key=os.getenv("OPENROUTER_API_KEY"),
        openrouter_base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
        llm_small_model=os.getenv("LLM_SMALL_MODEL"),
        llm_medium_model=os.getenv("LLM_MEDIUM_MODEL"),
        planner_model_size=os.getenv("PLANNER_MODEL_SIZE", "medium"),
        executor_model_size=os.getenv("EXECUTOR_MODEL_SIZE", "small"),
        validator_model_size=os.getenv("VALIDATOR_MODEL_SIZE", "small"),
        orchestrator_model_size=os.getenv("ORCHESTRATOR_MODEL_SIZE", "small"),
        chroma_persist_directory=Path(os.getenv("CHROMA_PERSIST_DIRECTORY", "./data/chroma")),
        jira_mcp_url=os.getenv("JIRA_MCP_URL"),
        jira_api_token=os.getenv("JIRA_API_TOKEN"),
        jira_email=os.getenv("JIRA_EMAIL"),
        plans_directory=Path(os.getenv("PLANS_DIRECTORY", "./plans")),
        max_retry_attempts=int(os.getenv("MAX_RETRY_ATTEMPTS", "3")),
    )
