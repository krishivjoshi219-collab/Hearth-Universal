"""Vendored re-export of the standalone `mcp-strands-adapter` package.

This module exists so the main project can import the bridge without adding the
standalone package to `sys.path`. The implementation lives in exactly one place:

    open-source-contribution/mcp-strands-adapter/mcp_strands_adapter/adapter.py

There is deliberately no second copy of the logic here. An earlier revision kept a
duplicated 80-line implementation here, which meant the library shipped in the
Open Source Mini Challenge submission and the code exercised by this project's
tests could silently drift apart.
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path
from typing import Any

_PKG_DIR = (
    Path(__file__).resolve().parents[2]
    / "open-source-contribution"
    / "mcp-strands-adapter"
    / "mcp_strands_adapter"
)


def _load_standalone() -> Any:
    """Import the standalone package by path, registering it as a real module."""
    init = _PKG_DIR / "__init__.py"
    if not init.exists():  # pragma: no cover - only if the repo layout changes
        raise ImportError(
            f"standalone mcp-strands-adapter package not found at {_PKG_DIR}. "
            f"Expected the open-source-contribution/ directory in this repository."
        )
    if "mcp_strands_adapter" in sys.modules:
        return sys.modules["mcp_strands_adapter"]
    spec = importlib.util.spec_from_file_location(
        "mcp_strands_adapter", init, submodule_search_locations=[str(_PKG_DIR)]
    )
    if spec is None or spec.loader is None:  # pragma: no cover
        raise ImportError(f"cannot load mcp_strands_adapter from {_PKG_DIR}")
    module = importlib.util.module_from_spec(spec)
    sys.modules["mcp_strands_adapter"] = module
    spec.loader.exec_module(module)
    return module


_mod = _load_standalone()

MCPServerBridge = _mod.MCPServerBridge
StrandsMCPToolBridge = _mod.StrandsMCPToolBridge
strands_available = _mod.strands_available
to_mcp_tool = _mod.to_mcp_tool

__all__ = [
    "MCPServerBridge",
    "StrandsMCPToolBridge",
    "strands_available",
    "to_mcp_tool",
]