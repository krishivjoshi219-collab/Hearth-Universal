"""mcp-strands-adapter: serve AWS Strands agents over the Model Context Protocol."""
from .adapter import (
    MCPServerBridge,
    StrandsMCPToolBridge,
    strands_available,
    to_mcp_tool,
)

__version__ = "0.2.0"
__all__ = [
    "MCPServerBridge",
    "StrandsMCPToolBridge",
    "strands_available",
    "to_mcp_tool",
    "__version__",
]