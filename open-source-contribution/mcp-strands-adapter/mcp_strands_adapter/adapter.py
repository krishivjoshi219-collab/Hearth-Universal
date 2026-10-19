"""mcp-strands-adapter: serve AWS Strands agents over the Model Context Protocol.

The gap this library fills
--------------------------
The Strands Agents SDK ships tooling to *consume* MCP servers. It does not ship
a way to *expose* Strands agents and tools to an MCP host such as Alexa+. This
adapter covers that direction: it converts Strands tools and agents into MCP
tool definitions and mounts them on a Streamable HTTP MCP server.

Why the schema handling is not reinvented here
----------------------------------------------
Strands derives tool schemas with Pydantic and ``docstring_parser``, producing a
``ToolSpec`` whose JSON Schema is nested at ``inputSchema.json``. MCP's wire
format expects that schema *flat* at ``inputSchema``. When you hand this adapter
an object that is already a Strands tool, it reuses the SDK's own
``tool_spec`` and only performs that reshaping -- it never re-derives a schema
the SDK has already derived correctly. Plain Python callables are still accepted
and fall back to signature-based reflection.

Example
-------
    from mcp.server.fastmcp import FastMCP
    from strands import Agent, tool
    from mcp_strands_adapter import MCPServerBridge

    @tool
    def tariff_shift(kwh: float) -> dict:
        \"\"\"Shift load off the peak tariff window.

        Args:
            kwh: energy to shift
        \"\"\"
        return {"shifted_kwh": kwh}

    mcp = FastMCP("household")
    MCPServerBridge(prefix="hearth_").register_all(mcp, [tariff_shift])
"""
from __future__ import annotations

import inspect
from collections.abc import Callable, Iterable
from typing import Any, get_type_hints

__all__ = [
    "MCPServerBridge",
    "StrandsMCPToolBridge",
    "strands_available",
    "to_mcp_tool",
]

_PY_TO_JSON: dict[Any, str] = {
    str: "string",
    int: "integer",
    float: "number",
    bool: "boolean",
    dict: "object",
    list: "array",
}


def strands_available() -> bool:
    """True when the optional ``strands-agents`` dependency can be imported."""
    try:  # pragma: no cover - trivial import probe
        import strands  # noqa: F401
    except Exception:
        return False
    return True


def _coerce(value: Any, annotation: Any) -> Any:
    """Best-effort coercion of a JSON scalar into the annotated Python type.

    MCP transports JSON, so an ``int`` parameter can legitimately arrive as a
    float (``3.0``) or a numeric string. Coercion is intentionally narrow: it
    never guesses container shapes, so a malformed call fails loudly at the
    callee rather than silently becoming something else.
    """
    if annotation in (int, float, str, bool) and not isinstance(value, (dict, list)):
        try:
            if annotation is bool:
                if isinstance(value, str):
                    return value.strip().lower() in ("1", "true", "yes", "on")
                return bool(value)
            if annotation is int:
                return int(value)
            if annotation is float:
                return float(value)
            if annotation is str:
                return str(value)
        except (TypeError, ValueError):
            return value
    return value


def _reflect_schema(fn: Callable[..., Any]) -> dict[str, Any]:
    """Signature-based JSON Schema for a plain callable.

    Only used for callables that are not Strands tools. Descriptions are lifted
    from the docstring's ``Args:`` block when present rather than emitted as
    "Parameter x" placeholders.
    """
    arg_docs = _parse_arg_docs(fn)
    try:
        hints = get_type_hints(fn)
    except Exception:
        hints = getattr(fn, "__annotations__", {}) or {}

    properties: dict[str, Any] = {}
    required: list[str] = []
    try:
        params = inspect.signature(fn).parameters
    except (TypeError, ValueError):
        params = {}
    for p_name, param in params.items():
        if p_name in ("self", "cls") or param.kind in (
            inspect.Parameter.VAR_POSITIONAL,
            inspect.Parameter.VAR_KEYWORD,
        ):
            continue
        annotation = hints.get(p_name, Any)
        prop: dict[str, Any] = {"type": _PY_TO_JSON.get(annotation, "string")}
        if p_name in arg_docs:
            prop["description"] = arg_docs[p_name]
        if param.default is inspect.Parameter.empty:
            required.append(p_name)
        else:
            try:
                if isinstance(param.default, (str, int, float, bool)) or param.default is None:
                    prop["default"] = param.default
            except Exception:
                pass
        properties[p_name] = prop
    return {"type": "object", "properties": properties, "required": required}


def _parse_arg_docs(fn: Callable[..., Any]) -> dict[str, str]:
    """Extract ``Args:`` entries from a Google-style docstring."""
    doc = inspect.getdoc(fn) or ""
    out: dict[str, str] = {}
    in_args = False
    for raw in doc.splitlines():
        line = raw.strip()
        if line.lower() in ("args:", "arguments:", "parameters:"):
            in_args = True
            continue
        if in_args:
            if not line:
                continue
            if line.lower() in ("returns:", "raises:", "yields:", "example:", "examples:"):
                break
            name, _, rest = line.partition(":")
            key = name.strip().split(" ")[0].strip("`")
            if key and rest.strip():
                out[key] = rest.strip()
    return out


def _unwrap_strands_tool(obj: Any) -> tuple[str | None, str, dict[str, Any], Callable[..., Any]] | None:
    """If ``obj`` is a Strands tool, return (name, description, json_schema, raw_fn).

    Recognises the SDK's ``DecoratedFunctionTool`` via duck-typing on
    ``tool_spec``, so the adapter works across SDK point releases without
    importing private classes. Returns ``None`` for a plain callable.
    """
    spec = getattr(obj, "tool_spec", None)
    if not isinstance(spec, dict) or "name" not in spec:
        return None
    name = spec.get("name")
    description = spec.get("description") or ""
    schema_container = spec.get("inputSchema") or {}
    json_schema = schema_container.get("json") if isinstance(schema_container, dict) else None
    if not isinstance(json_schema, dict):
        json_schema = schema_container if isinstance(schema_container, dict) else {}
    # The original undecorated function, when the SDK exposes it.
    raw = getattr(obj, "_tool_func", None) or getattr(obj, "__wrapped__", None) or obj
    return str(name), description, json_schema, raw


class MCPServerBridge:
    """Expose Strands tools and agents as MCP tools on a FastMCP server.

    Args:
        prefix: Optional name prefix applied to every exported tool, e.g.
            ``"hearth_"``. Applied unless the tool name already carries it.
    """

    def __init__(self, prefix: str = "") -> None:
        self.prefix = prefix
        self._tools: dict[str, Callable[..., Any]] = {}
        self._hints: dict[str, dict[str, Any]] = {}
        self._schemas: dict[str, dict[str, Any]] = {}

    # -- registration -------------------------------------------------------

    def add(self, obj: Any, name: str | None = None,
            description: str | None = None) -> dict[str, Any]:
        """Register one Strands tool, Agent, or plain callable as an MCP tool.

        Args:
            obj: A ``@tool``-decorated function, a ``strands.Agent``, or a plain callable.
            name: Override the exported tool name.
            description: Override the exported description.

        Returns:
            The MCP tool definition (name, description, inputSchema).
        """
        tool_name, tool_desc, json_schema, handler, hints = self._normalize(obj)

        exported = name or tool_name
        if self.prefix and not exported.startswith(self.prefix):
            exported = f"{self.prefix}{exported}"
        if description:
            tool_desc = description

        if not callable(handler):
            raise TypeError(
                f"'{exported}' is not invocable. Pass a @tool-decorated function, "
                f"an Agent with an .as_tool() result, or a plain callable."
            )

        definition = {
            "name": exported,
            "description": tool_desc,
            "inputSchema": json_schema,
        }
        self._tools[exported] = handler
        self._hints[exported] = hints
        self._schemas[exported] = definition
        return definition

    def add_all(self, objects: Iterable[Any]) -> list[dict[str, Any]]:
        """Register several objects at once, preserving order."""
        return [self.add(obj) for obj in objects]

    def register_all(self, mcp: Any, objects: Iterable[Any]) -> list[dict[str, Any]]:
        """Register objects and mount them on a FastMCP server instance.

        Each tool is wrapped so the MCP client-facing signature matches the
        original tool's JSON Schema, then bound with ``mcp.tool()``.
        """
        definitions = self.add_all(objects)
        for definition in definitions:
            exported = definition["name"]
            handler = self._tools[exported]
            hints = self._hints[exported]
            self._mount(mcp, exported, definition, handler, hints)
        return definitions

    # -- dispatch -----------------------------------------------------------

    def call(self, tool_name: str, arguments: dict[str, Any] | None = None) -> Any:
        """Invoke a registered tool the way an MCP ``tools/call`` would.

        Unknown tool names raise ``KeyError``; unexpected arguments raise
        ``TypeError`` rather than being silently dropped.
        """
        if tool_name not in self._tools:
            raise KeyError(
                f"MCP tool '{tool_name}' is not registered. "
                f"Available: {sorted(self._tools)}"
            )
        handler = self._tools[tool_name]
        args = dict(arguments or {})
        hints = self._hints.get(tool_name, {})
        coerced = {k: _coerce(v, hints.get(k, Any)) for k, v in args.items()}
        return handler(**coerced)

    def list_tools(self) -> list[dict[str, Any]]:
        """All MCP tool definitions, ready for a ``tools/list`` response."""
        return list(self._schemas.values())

    @property
    def tool_names(self) -> list[str]:
        return list(self._tools)

    # -- internals ----------------------------------------------------------

    def _normalize(self, obj: Any) -> tuple[str, str, dict[str, Any], Any, dict[str, Any]]:
        unwrapped = _unwrap_strands_tool(obj)
        if unwrapped is not None:
            name, desc, schema, raw = unwrapped
            # An AgentTool (what Agent.as_tool() returns) exposes an async
            # .stream() rather than __call__, so it needs a sync adapter.
            if not callable(raw) and hasattr(raw, "stream"):
                return name, desc, schema or {"type": "object", "properties": {}}, \
                    _AgentToolHandler(raw, name), {}
            hints = self._annotations_of(raw)
            return name, desc, schema or {"type": "object", "properties": {}}, raw, hints
        # A bare Agent: prefer .as_tool() so the SDK handles delegation.
        if hasattr(obj, "as_tool") and callable(obj.as_tool):
            as_tool = obj.as_tool()
            inner = _unwrap_strands_tool(as_tool)
            if inner is not None:
                name, desc, schema, raw = inner
                handler = raw if callable(raw) else _AgentToolHandler(raw, name)
                return name, desc, schema, handler, {}
        if callable(obj):
            name = getattr(obj, "__name__", "tool")
            desc = inspect.getdoc(obj) or f"Exposed callable {name}"
            return name, desc, _reflect_schema(obj), obj, self._annotations_of(obj)
        raise TypeError(f"Cannot export {type(obj).__name__} as an MCP tool")

    @staticmethod
    def _annotations_of(fn: Any) -> dict[str, Any]:
        try:
            return get_type_hints(fn)
        except Exception:
            return getattr(fn, "__annotations__", {}) or {}

    def _mount(self, mcp: Any, exported: str, definition: dict[str, Any],
               handler: Callable[..., Any], hints: dict[str, Any]) -> None:
        """Bind one tool onto a FastMCP server, preserving its input schema."""
        schema = definition.get("inputSchema") or {}
        props = schema.get("properties") or {}
        properties = list(props.keys())
        required = set(schema.get("required") or [])

        # FastMCP derives its own schema from the wrapper signature, so rebuild a
        # signature whose parameters match the exported JSON Schema exactly --
        # including each parameter's declared default, so the mounted schema
        # stays identical to the definition we advertise.
        params = []
        for p_name in properties:
            if p_name in required:
                default: Any = ...
            else:
                declared = props[p_name].get("default")
                default = declared if declared is not None else None
            params.append(_param(hints.get(p_name, Any), p_name, default))
        wrapper = _build_wrapper(handler, hints, properties, exported)
        wrapper.__name__ = exported
        wrapper.__doc__ = definition.get("description") or handler.__doc__
        wrapper.__signature__ = inspect.Signature(params)  # type: ignore[attr-defined]
        wrapper.__annotations__ = {p.name: p.annotation for p in params}

        mcp.tool(name=exported, description=definition.get("description"))(wrapper)


def _param(annotation: Any, name: str, default: Any) -> inspect.Parameter:
    return inspect.Parameter(
        name,
        inspect.Parameter.KEYWORD_ONLY,
        annotation=annotation,
        default=default,
    )


class _AgentToolHandler:
    """Adapt a Strands ``AgentTool`` (from ``Agent.as_tool()``) to a sync callable.

    ``AgentTool.stream()`` is an async generator yielding ``ToolResultEvent``
    objects. MCP ``tools/call`` is synchronous, so this drains the generator on a
    private event loop and returns the final text payload. An SDK-declared error
    is raised so the MCP layer can surface it as a tool error rather than
    pretending the call succeeded.
    """

    def __init__(self, agent_tool: Any, tool_name: str) -> None:
        self._agent_tool = agent_tool
        self._tool_name = tool_name

    def __call__(self, **kwargs: Any) -> Any:
        import asyncio
        import uuid as _uuid

        tool_use = {
            "toolUseId": _uuid.uuid4().hex,
            "name": self._tool_name,
            "input": dict(kwargs),
        }

        async def _drain() -> Any:
            text_parts: list[str] = []
            status = "success"
            async for event in self._agent_tool.stream(tool_use, {}):
                result = getattr(event, "tool_result", None)
                if not isinstance(result, dict):
                    continue
                if result.get("status") == "error":
                    status = "error"
                for block in result.get("content") or []:
                    if isinstance(block, dict) and block.get("text"):
                        text_parts.append(str(block["text"]))
            return status, "\n".join(p for p in text_parts if p)

        try:
            loop = asyncio.new_event_loop()
            try:
                status, text = loop.run_until_complete(_drain())
            finally:
                loop.close()
        except RuntimeError:
            # Already inside a running loop (e.g. an async MCP server).
            status, text = asyncio.run(_drain())
        if status == "error":
            raise RuntimeError(text or f"Strands tool '{self._tool_name}' returned an error")
        return text


def _build_wrapper(handler: Callable[..., Any], hints: dict[str, Any],
                   properties: list[str], exported: str) -> Callable[..., Any]:
    def _call(**kwargs: Any) -> Any:
        allowed = set(properties)
        unexpected = set(kwargs) - allowed
        if unexpected:
            raise TypeError(
                f"tool '{exported}' received unexpected argument(s): {sorted(unexpected)}"
            )
        coerced = {k: _coerce(v, hints.get(k, Any)) for k, v in kwargs.items()}
        return handler(**coerced)

    _call.__name__ = exported
    return _call


def to_mcp_tool(obj: Any, prefix: str = "") -> dict[str, Any]:
    """One-shot conversion of a Strands tool to an MCP tool definition.

    Args:
        obj: A ``@tool``-decorated function, a ``strands.Agent``, or a callable.
        prefix: Optional exported name prefix.

    Returns:
        The MCP tool definition dict.
    """
    return MCPServerBridge(prefix=prefix).add(obj)


# Backwards-compatible alias from the original package name.
StrandsMCPToolBridge = MCPServerBridge