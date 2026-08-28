# Architecture

## Purpose

This project turns a Markdown or text business use case into a persisted JSON execution plan and runs that plan through explicit agent contracts.

## Boundaries

- `rag_framework.config`: environment-backed settings and paths.
- `rag_framework.domain`: typed plan, task, input, retry, and execution contracts.
- `rag_framework.schemas`: JSON Schema documents and validation helpers.
- `rag_framework.registry`: model and tool discovery/dispatch.
- `rag_framework.persistence`: atomic local plan storage and resume support.
- `rag_framework.agents`: planner, task executor, subtask executor, and validator.
- `rag_framework.orchestrator`: dependency scheduling and the only plan-state mutation boundary.
- `rag_framework.transformer`: validated output-to-input mappings between tasks.
- `rag_framework.tools`: document, ChromaDB, and MCP adapters.
- `rag_framework.cli`: user-facing plan, execution, resume, and goal-trigger commands.

## Rules

1. The persisted plan JSON is the execution source of truth.
2. The Orchestrator alone changes plan execution state.
3. Planner, executors, and Validator communicate through schema-validated JSON contracts.
4. Every tool request is discovered and dispatched through `ToolRegistry`.
5. Every model request is resolved through `ModelRegistry`.
6. Planner does not execute tools; executors do not mutate the master plan; Validator does not mutate the master plan.
7. Tool-only tasks do not invoke a model.
8. Automatic retries are capped at three attempts and carry failure context.
9. External providers are adapters and are injectable in tests.

## Execution flow

`use-case file -> Planner -> PlanStore -> Orchestrator -> Executor -> Validator -> PlanStore`

The orchestrator resolves inputs and dependencies, generates contracts, persists each transition, propagates validated outputs, and either retries, continues independent work, recovers, or pauses on failure.

## Initial implementation policy

The first implementation is synchronous and offline by default. OpenRouter and JIRA MCP interfaces are represented by testable adapters, while deterministic local embeddings make the acceptance flow runnable without credentials. ChromaDB support is optional and isolated behind the tool boundary.
