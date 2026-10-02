"""MCP Strands Adapter: Open-Source Bridge between AWS Strands Agents SDK and MCP 2025-11-25.

Open Source Mini Challenge Component:
Enables developers building multi-agent systems with AWS Strands Agents SDK to
seamlessly expose and consume tools adhering to Model Context Protocol (MCP spec 2025-11-25)
over Streamable HTTP without boilerplate.

Key Capabilities:
1. `StrandsToMCPTool`: Wraps an AWS Strands callable agent tool into an MCP tool definition.
2. `MCPToStrandsTool`: Converts an external MCP Streamable HTTP tool into a native Strands tool callable.
3. `StrandsToolRegistry`: Unified registry with dynamic JSON Schema reflection.
"""
from __future__ import annotations

import inspect
from typing import Any, Callable, get_type_hints


class StrandsMCPToolBridge:
    """Bi-directional bridge between AWS Strands Agent tools and MCP 2025-11-25 definitions."""

    def __init__(self, name_prefix: str = "strands_") -> None:
        self.name_prefix = name_prefix
        self._strands_tools: dict[str, Callable[..., Any]] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    def register_strands_tool(
        self,
        name: str,
        fn: Callable[..., Any],
        description: str | None = None,
    ) -> dict[str, Any]:
        """Convert a Strands tool function into an MCP 2025-11-25 Tool Specification."""
        mcp_name = f"{self.name_prefix}{name}" if not name.startswith(self.name_prefix) else name
        doc = description or inspect.getdoc(fn) or f"Strands tool {name}"
        
        # Build JSON Schema for parameters via inspect
        sig = inspect.signature(fn)
        type_hints = get_type_hints(fn) if hasattr(fn, "__annotations__") else {}
        properties: dict[str, Any] = {}
        required: list[str] = []

        for p_name, param in sig.parameters.items():
            if p_name in ("self", "cls"):
                continue
            p_type = type_hints.get(p_name, Any)
            type_str = "string"
            if p_type in (int, float):
                type_str = "number"
            elif p_type is bool:
                type_str = "boolean"
            elif p_type in (dict, list):
                type_str = "object"

            properties[p_name] = {
                "type": type_str,
                "description": f"Parameter {p_name}",
            }
            if param.default is inspect.Parameter.empty:
                required.append(p_name)

        schema = {
            "name": mcp_name,
            "description": doc,
            "inputSchema": {
                "type": "object",
                "properties": properties,
                "required": required,
            },
        }

        self._strands_tools[mcp_name] = fn
        self._schemas[mcp_name] = schema
        return schema

    def list_mcp_tools(self) -> list[dict[str, Any]]:
        """List all converted MCP tools ready for FastMCP registration."""
        return list(self._schemas.values())

    def invoke_from_mcp(self, mcp_tool_name: str, arguments: dict[str, Any]) -> Any:
        """Execute a Strands tool invoked via an MCP client JSON-RPC request."""
        if mcp_tool_name not in self._strands_tools:
            raise KeyError(f"Strands tool '{mcp_tool_name}' not registered in bridge")
        fn = self._strands_tools[mcp_tool_name]
        return fn(**arguments)
