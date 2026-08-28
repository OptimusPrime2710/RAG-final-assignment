"""Register reusable document and semantic-search tools."""

from typing import Any

from rag_framework.registry.tool_registry import ToolDescriptor, ToolRegistry
from rag_framework.tools.chroma import ChromaStore
from rag_framework.tools.document import index_directory


def register_rag_tools(registry: ToolRegistry, store: Any) -> None:
    registry.register(
        ToolDescriptor(
            "rag.index_directory", "index_directory", "Incrementally index text documents", "python",
            input_schema={"type": "object", "required": ["directory"], "properties": {"directory": {"type": "string"}}},
            output_schema={"type": "object", "required": ["processed", "skipped"]}, capabilities=["rag", "indexing"],
        ),
        lambda inputs: index_directory(inputs["directory"], store),
    )
    registry.register(
        ToolDescriptor(
            "rag.search_similar", "search_similar", "Search indexed documents", "python",
            input_schema={"type": "object", "required": ["query"], "properties": {"query": {"type": "string"}, "top_k": {"type": "integer", "minimum": 1}}},
            output_schema={"type": "object", "required": ["results"]}, capabilities=["rag", "retrieval"],
        ),
        lambda inputs: {"results": store.search_similar(inputs["query"], inputs.get("top_k", 5))},
    )
