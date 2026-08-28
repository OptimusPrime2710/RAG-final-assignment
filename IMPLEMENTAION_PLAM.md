Below is a concise, implementation-oriented prompt you can save directly as IMPLEMENTATION_PLAN.md and give to your coding agent. It is intentionally written to make the agent inspect first, implement step-by-step, validate each step, and avoid unnecessary architectural changes.

Multi-Agent Business Use-Case Planning and Execution Framework
1. Objective

Build a Python-based, plan-driven multi-agent framework that accepts a business use case from a .txt or .md file, creates an executable JSON plan, persists it locally, and executes the plan through specialized agents.

The system must support:

Planner Agent
Orchestrator
Task Executor Agent
Subtask Executor Agent
Validator Agent
Tool Registry
Model Registry
Contract Generator/Transformer
Local JSON Plan Store
Retry and recovery mechanism
Dynamic tool discovery
OpenRouter for LLM access
JIRA Cloud MCP for JIRA operations
ChromaDB for semantic search/vector storage

Do not unnecessarily change existing project architecture. First inspect the repository and reuse existing abstractions wherever possible.

2. Mandatory Implementation Process

The coding agent must work step-by-step.

Before implementing each step:

Inspect the existing code relevant to that step.
Identify reusable components.
Explain internally what needs to change.
Implement only the required changes.
Run relevant tests/type checks/linting.
Fix failures.
Verify the step is complete.
Only then continue to the next step.

Do not implement the entire system blindly in one pass.

Maintain a progress file:

IMPLEMENTATION_PROGRESS.md


Update it after every completed step with:

## Step N - <name>
Status: COMPLETE

Implemented:
- ...

Tests:
- ...

Validation:
- ...

Notes:
- ...


If a step cannot be completed, mark it:

Status: BLOCKED


and document the reason instead of silently moving forward.

3. Step 1 — Inspect Existing Project

Inspect:

Repository structure
Python version
Existing agents
Existing LLM integration
Existing tool abstraction
Existing MCP integration
Existing configuration system
Existing persistence
Existing tests
Existing ChromaDB integration, if any

Do not duplicate existing functionality.

Create/update:

ARCHITECTURE.md


with the proposed integration points before major implementation begins.

4. Step 2 — Configuration

Use .env for configuration.

LLMs must be accessed through OpenRouter.

Example:

OPENROUTER_API_KEY=<secret>

LLM_SMALL_MODEL=<openrouter-model>
LLM_MEDIUM_MODEL=<openrouter-model>

PLANNER_MODEL_SIZE=medium
EXECUTOR_MODEL_SIZE=small
VALIDATOR_MODEL_SIZE=small
ORCHESTRATOR_MODEL_SIZE=small

CHROMA_PERSIST_DIRECTORY=./data/chroma

JIRA_MCP_URL=<jira-cloud-mcp-url>


Do not commit secrets.

Do not hardcode model names.

Implement a ModelRegistry.

Agents request:

small
medium


and the registry resolves the configured OpenRouter model.

A task may explicitly require:

{
  "required": true,
  "size": "small"
}


or:

{
  "required": false
}


Tool-only tasks must not invoke an LLM unnecessarily.

5. Step 3 — Tool Registry

Create a central tool registry.

Every tool must expose:

{
  "toolid": "unique-id",
  "tool_name": "tool-name",
  "description": "description",
  "type": "python|api|mcp",
  "input_schema": {},
  "output_schema": {},
  "capabilities": [],
  "enabled": true
}


Support:

Python functions
Python APIs
MCP tools

Agents must dynamically discover tools through the registry.

LLM-generated tool requests must never bypass the registry.

6. Step 4 — JIRA Cloud MCP

Integrate JIRA Cloud through MCP.

JIRA MCP tools must appear in the same Tool Registry as Python tools.

The Executor must not care whether a tool is:

Python
API
MCP


All must use a common execution interface.

Example capabilities:

jira
jira_issue_creation
jira_issue_search
jira_issue_update


Do not hardcode JIRA-specific behavior into the generic executor.

7. Step 5 — ChromaDB

Use ChromaDB for semantic search.

Create reusable tools for at least:

create_collection
load_document
generate_embedding
store_embedding
search_similar
validate_collection


The exact implementation may use the project's existing embedding/model infrastructure where available.

Support:

Document location
    ↓
Read document
    ↓
Extract text
    ↓
Chunk text
    ↓
Generate embeddings
    ↓
Store in ChromaDB


Persist ChromaDB locally using the configured directory.

8. Step 6 — Business Use-Case Input

Planner accepts:

.txt
.md
.markdown


Example:

# Semantic Search

Load documents from ./documents into ChromaDB.

Users should be able to search the documents using natural language.

Return the top 5 most relevant documents.


The Planner must extract:

Business objective
Goals
Inputs
Defaults
Constraints
Tasks
Subtasks
Dependencies
Required tools
Success criteria
Criticality
Model requirements
9. Step 7 — Plan JSON

The plan is the single source of truth.

Save plans locally:

plans/
  plan_<plan_id>.json


Minimum structure:

{
  "plan_id": "plan_001",
  "version": 1,
  "status": "pending",
  "source": {},
  "use_case": {},
  "inputs": [],
  "goals": [
    {
      "goal_id": "goal_001",
      "goal": "...",
      "description": "...",
      "status": "pending",
      "critical": true,
      "success_criteria": [
        {
          "criterion_id": "criteria_001",
          "description": "...",
          "achieved": false
        }
      ],
      "tasks": [
        {
          "task_id": "task_001",
          "task": "...",
          "description": "...",
          "status": "pending",
          "critical": true,
          "dependencies": [],
          "inputs": {},
          "expected_output": {},
          "model_requirement": {
            "required": false,
            "size": null
          },
          "tool_required": [],
          "subtasks": [],
          "retry": {
            "attempt": 0,
            "max_attempts": 3,
            "last_error": null,
            "failure_input": null
          },
          "execution": {}
        }
      ]
    }
  ]
}


Use explicit statuses:

pending
ready
running
completed
failed
blocked
skipped
paused

10. Step 8 — Inputs and Defaults

Plans must support user inputs and defaults.

Example:

{
  "input_id": "top_k",
  "name": "top_k",
  "type": "integer",
  "required": false,
  "user_value": null,
  "default_value": 5,
  "effective_value": 5,
  "source": "default"
}


Rules:

User value overrides default.
Default is used when user does not provide a value.
Missing required input blocks execution.
Task outputs can become downstream task inputs.
11. Step 9 — Planner Agent

Planner responsibilities:

Analyze business use case.
Create one or more goals.
Create measurable success criteria.
Create tasks.
Create subtasks where appropriate.
Define dependencies.
Identify critical tasks.
Discover appropriate tools.
Determine model requirements.
Identify reusable capabilities.
Define recovery considerations.

Planner must not execute tools or tasks.

Planner returns structured JSON only.

Use the configured PLANNER_MODEL_SIZE.

12. Step 10 — Standard Executor Contract

All executors must receive the same basic JSON contract:

{
  "request_id": "req_001",
  "plan_id": "plan_001",
  "goal_id": "goal_001",
  "task_id": "task_001",
  "subtask_id": null,
  "executor_type": "task_executor",
  "task": {
    "name": "...",
    "description": "..."
  },
  "inputs": {},
  "tools": [],
  "model_requirement": {
    "required": false,
    "size": null
  },
  "success_criteria": [],
  "attempt": 1,
  "max_attempts": 3,
  "previous_failure": null
}


Validate this contract using JSON Schema.

13. Step 11 — Executor Agent

Executor responsibilities:

Validate request.
Discover/verify tools.
Resolve model from Model Registry if required.
Execute assigned task.
Perform basic self-validation.
Return structured JSON.
Never directly modify the master plan.

Response:

{
  "request_id": "req_001",
  "status": "success",
  "result": {},
  "output_for_next_executor": {},
  "validation": {
    "status": "passed",
    "checks": []
  },
  "error": null,
  "retry": {
    "required": false,
    "attempt": 1,
    "max_attempts": 3,
    "failure_input": null
  }
}


Never fabricate tool results.

14. Step 12 — Subtask Executor

If a task contains subtasks, execute them through sub-executor contracts.

Example:

Task: Populate ChromaDB

Subtasks:
1. Discover files
2. Read file
3. Extract text
4. Chunk text
5. Generate embeddings
6. Store embeddings
7. Validate indexed data


Respect dependencies.

Independent subtasks may execute concurrently if safe.

15. Step 13 — Validator Agent

Use two levels of validation.

Executor validation

Basic operational checks.

Validator Agent

Independent business/semantic validation.

Validator receives:

{
  "plan_id": "...",
  "goal_id": "...",
  "task_id": "...",
  "success_criteria": [],
  "executor_result": {},
  "executor_validation": {}
}


Returns:

{
  "status": "passed",
  "criteria": [
    {
      "criterion_id": "...",
      "passed": true,
      "evidence": "..."
    }
  ],
  "reason": null,
  "retry_recommended": false
}


Validator must not directly modify the master plan.

16. Step 14 — Orchestrator

The Orchestrator owns execution state.

Flow:

Load Plan
   ↓
Resolve Inputs
   ↓
Find Ready Task
   ↓
Generate Executor Contract
   ↓
Execute
   ↓
Executor Self-Validation
   ↓
Validator Agent
   ↓
Update Plan
   ↓
Retry / Continue / Recover
   ↓
Find Next Ready Task


Only the Orchestrator modifies plan execution state.

17. Step 15 — Contract Transformation

Executor output must be convertible into the next executor's input.

Never pass uncontrolled natural-language responses between executors.

Use:

Executor A output
      ↓
Contract Transformer
      ↓
Validate against Executor B input schema
      ↓
Executor B


If mapping fails:

CONTRACT_MAPPING_FAILED


and do not execute the next task.

18. Step 16 — Retry and Recovery

Maximum attempts:

3


A retry must include previous failure information.

Example:

{
  "previous_failure": {
    "attempt": 1,
    "error": "...",
    "tool": "...",
    "input": {},
    "validator_feedback": {},
    "recommended_correction": "..."
  }
}


Do not blindly repeat the same failed operation.

After 3 failures:

Task → failed
        ↓
Planner evaluates impact


For non-critical tasks:

Continue independent work where possible.


For critical tasks:

Attempt recovery/replanning.
If recovery is not possible → pause/escalate.

19. Step 17 — Goal Retriggering

Goals must be independently retriggerable by the user after the original plan is created.

This is a core requirement.

Example goals:

goal_001:
Populate ChromaDB

goal_002:
Retrieve semantically similar documents


A user can later request:

"Populate ChromaDB with the new documents in ./new_documents"


The system should resolve the existing population goal and execute it.

Or:

"Find the top 5 documents related to customer cancellation policy."


The system should resolve the existing retrieval goal and execute it without rebuilding the database.

20. Semantic Retrieval Goal

Create a reusable retrieval capability:

Goal:
Retrieve semantically similar documents


Typical execution:

User query
    ↓
Resolve top_k
    ↓
Generate query embedding
    ↓
Search ChromaDB
    ↓
Retrieve top K
    ↓
Validate results
    ↓
Return relevant files/results


Default:

top_k = 5


unless the user specifies another value.

21. ChromaDB Population Goal

Create a reusable goal:

Goal:
Populate/Update ChromaDB


It must support:

Initial population
New documents
Incremental updates
Re-indexing where required
Validation of indexed documents

Example:

User:
"Add all new Markdown files from ./new_docs to semantic search."


The goal should execute only the necessary population/indexing work.

Do not rebuild the entire database unnecessarily.

22. Step 18 — Persistence and Resume

Every state transition must be persisted.

Use atomic JSON writes.

The system must be able to restart and resume a partially completed plan.

Example:

Task 1 completed
Task 2 completed
Task 3 running
Process crashes
       ↓
Restart
       ↓
Load plan JSON
       ↓
Resume safely


Do not repeat completed tasks unless explicitly required.

23. Step 19 — Model Usage

Track model usage where possible:

{
  "model_execution": {
    "provider": "openrouter",
    "model": "...",
    "size": "small",
    "purpose": "task_execution",
    "plan_id": "...",
    "task_id": "...",
    "request_id": "..."
  }
}


Capture token usage/latency/cost when available.

24. Step 20 — Testing

Add tests for:

TXT planning
Markdown planning
Multiple goals
Tasks/subtasks
Dependencies
User input overriding defaults
Default values
Missing required inputs
Tool discovery
Python tool execution
MCP tool execution
JIRA MCP
ChromaDB population
ChromaDB retrieval
Small model selection
Medium model selection
Tool-only execution without an LLM
Executor validation
Validator validation
Contract transformation
Retry attempt 1/2/3
Failure after 3 attempts
Critical task failure
Non-critical task failure
Recovery/replanning
Goal retriggering
Plan persistence
Resume after restart
25. Final End-to-End Acceptance Test

The implementation must demonstrate this complete workflow:

business_use_case.md
        ↓
Planner Agent
        ↓
Plan JSON
        ↓
Local persistence
        ↓
Orchestrator
        ↓
Goal: Populate ChromaDB
        ↓
Task/Subtask Executors
        ↓
Python + ChromaDB tools
        ↓
Executor validation
        ↓
Validator Agent
        ↓
Plan update
        ↓
Goal completed


Then demonstrate:

User:
"Find the top 5 documents about cancellation policy."
        ↓
Existing retrieval goal resolved
        ↓
Retrieval executor
        ↓
ChromaDB semantic search
        ↓
Validator
        ↓
Top 5 results


Then demonstrate:

User:
"Add new documents from ./new_documents."
        ↓
Existing population goal resolved
        ↓
Only new documents processed
        ↓
ChromaDB updated
        ↓
Validator
        ↓
Plan updated


Also demonstrate a failed executor:

Attempt 1 → failure
Attempt 2 → failure
Attempt 3 → failure
        ↓
Task marked failed
        ↓
Planner evaluates criticality
        ↓
Recovery OR pause/escalation

26. Non-Negotiable Architecture Rules
Plan JSON is the source of truth.
Orchestrator owns plan state.
Planner does not execute tasks.
Executor does not modify the master plan.
Validator independently validates execution.
All agent communication uses JSON contracts.
All contracts are schema validated.
All tools go through the Tool Registry.
All models go through the Model Registry.
OpenRouter is the LLM gateway.
JIRA Cloud is accessed through MCP.
ChromaDB is used for semantic search.
Model names are configuration-driven.
Secrets are never hardcoded.
Tasks may explicitly require small/medium/no model.
Failed tasks receive failure context on retry.
Maximum automatic retries = 3.
Critical failures may pause/escalate.
Goals are reusable and user-retriggerable.
Do not rebuild existing capabilities unnecessarily.
Do not modify unrelated project functionality.
Complete and validate each implementation step before proceeding.
27. Deliverables

At completion, provide:

IMPLEMENTATION_PROGRESS.md
ARCHITECTURE.md
Updated source code
.env.example
JSON schemas
Tests
Example business use case
Example generated plan
Example executor request
Example executor response
Example validator response
README updates


The README must explain how to:

Configure OpenRouter.
Configure JIRA Cloud MCP.
Configure ChromaDB.
Create a business use-case file.
Generate a plan.
Execute a plan.
Trigger an existing goal.
Populate ChromaDB.
Perform semantic retrieval.
Resume a failed/interrupted plan.

Do not finish by merely describing the architecture. Implement it, test it, and demonstrate the complete end-to-end workflow.

This is ready to save as IMPLEMENTATION_PLAN.md and hand directly to the coding agent.