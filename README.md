# Multi-Agent RAG Framework

Plan-driven business use-case execution with typed JSON contracts, local persistence, tool registries, and semantic retrieval.

## Setup

Requires Python 3.11 or newer.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev,rag]"
```

Copy `.env.example` to `.env`. Configure `OPENROUTER_API_KEY` and model names when live model access is enabled. Configure `JIRA_MCP_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` for Jira Cloud MCP. Plans are saved under `PLANS_DIRECTORY`; local vector data defaults to `data/chroma`.

For a model-required executor, connect `OpenRouterGateway.execute_request` to `TaskExecutorAgent(model_call=...)`. The gateway sends JSON-only requests and records provider, model, latency, and token usage metadata.

For JIRA Cloud MCP, load `JIRA_MCP_URL`, `JIRA_EMAIL`, and `JIRA_API_TOKEN` from settings, create `JiraMCPAdapter.from_url(settings.jira_mcp_url, api_token=settings.jira_api_token, email=settings.jira_email)`, and register the required operations with `register_tools`. They then execute through `ToolRegistry` like local tools:

```python
adapter = JiraMCPAdapter.from_url(settings.jira_mcp_url)
adapter.register_tools(registry, ["issue_search", "issue_create"])
```

## Workflow

The Planner accepts `.txt`, `.md`, and `.markdown` files and creates a JSON plan. The Orchestrator executes ready tasks, persists every state transition, validates results, and retries failures up to three times.

```powershell
rag-framework
python -m pytest -q
```

Run a secret-safe preflight before enabling integrations:

```powershell
rag-framework config-check --openrouter --jira
```

Retrigger an existing reusable goal with a later request:

```powershell
rag-framework goal 001 "Find the top 5 documents about cancellation policy"
```

Use configured Jira MCP tools explicitly during plan execution:

```powershell
rag-framework execute 001 --live-jira
```

This performs MCP initialization and `tools/list` discovery before execution. Offline commands do not contact Jira.

Run a controlled simple or complex business query:

```powershell
python -m rag_framework.cli query "Users are being forced to authenticate several times during the same work session."
python -m rag_framework.cli query "What is the average word count in the top 5 documents similar to INC-0005?" --top-k 5 --live-model
```

Simple queries return retrieved evidence. Complex queries compute from retrieved evidence and may use OpenRouter for final JSON synthesis when `--live-model` is enabled. If no matching evidence exists, the result is `No response found`; no model call is made for that case.

Override declared plan inputs at execution time with repeated `--input` options:

```powershell
rag-framework goal 001 "Find documents" --input top_k=10
```

The offline components are available as Python APIs:

```python
from rag_framework.agents.planner import PlannerAgent
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.document import index_directory

plan = PlannerAgent().create_plan("examples/business_use_case.md", "001")
store = ChromaStore()
index_directory("documents", store)
results = store.search_similar("cancellation policy", top_k=5)
```

`top_k` defaults to 5 and can be overridden through plan inputs. Re-indexing skips unchanged files. A persisted plan can be loaded with `PlanStore` and passed back to the Orchestrator to resume incomplete work. JIRA operations use the same Tool Registry interface as Python tools and are currently represented by a mockable MCP adapter.

Search uses hybrid ranking: exact phrases and shared incident terms are ranked ahead of unrelated vector matches. This ensures an exact issue description such as an `INC-0005` sentence returns that incident first.

The default offline `ChromaStore` needs no service dependency. Install the `rag` extra to use `NativeChromaStore` with a local ChromaDB `PersistentClient`.

## Project layout

- `src/rag_framework/domain.py`: typed plans and JSON contracts
- `src/rag_framework/agents/`: planner, executor, subtask executor, validator
- `src/rag_framework/orchestrator.py`: execution state owner
- `src/rag_framework/registry/`: model and tool registries
- `src/rag_framework/tools/`: document, vector, and MCP adapters
- `plans/`: persisted plans (ignored by Git)
- `examples/`: sample input and contract artifacts
