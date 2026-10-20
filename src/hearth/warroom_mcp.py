"""Standalone stdio FastMCP server for direct Antigravity <-> OpenCode War Room communication.

Can be run directly via:
  python3 -m hearth.warroom_mcp
"""

from __future__ import annotations

from typing import Annotated

from mcp.server.fastmcp import FastMCP
from pydantic import Field

from hearth import warroom

mcp = FastMCP("HearthWarRoom")


@mcp.tool()
def warroom_agent_broadcast(
    sender: Annotated[str, Field(description="Agent identifier: 'opencode' or 'gemini'")],
    message: Annotated[str, Field(description="Message content to broadcast to other agents")],
    topic: Annotated[str, Field(description="Topic/domain: e.g. 'film', 'presentation', 'security'")] = "general",
) -> dict:
    """Broadcast an inter-agent war room dispatch logged to IPC and discussion.md."""
    return warroom.send_message(sender=sender, message=message, topic=topic)


@mcp.tool()
def warroom_agent_inbox(
    limit: Annotated[int, Field(description="Max messages to retrieve")] = 10,
) -> dict:
    """Retrieve recent inter-agent dispatches from the war room bus."""
    return {"messages": warroom.get_messages(limit=limit)}


@mcp.tool()
def warroom_agent_status() -> dict:
    """Get high-level status of the two-agent war room and master assets."""
    return warroom.get_warroom_status()


if __name__ == "__main__":
    mcp.run()
