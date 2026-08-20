"""
service_request_tools.py — MCP Server for City Service Triage Agent

This file exposes three tools that an AI agent can call via the
Model Context Protocol (MCP):

  1. list_requests    — get all requests with optional filters
  2. get_request      — get one request by ID
  3. update_request_status — update the status of a request

How it works:
- The MCP server runs as a separate process alongside FastAPI
- It calls your FastAPI REST API internally using httpx
- AI agents connect to this MCP server and call tools by name
- The MCP library handles all protocol details automatically

Why call the API instead of the database directly?
- Keeps business logic in one place (the API)
- MCP server stays thin — just a translation layer
- If the API changes, only one place needs updating
- Consistent validation (API validates inputs, MCP inherits that)
"""

import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

# Base URL of your FastAPI server
# MCP server calls this internally to interact with your data
API_BASE = "http://127.0.0.1:8000"

# Create the MCP server instance
# The name "city-service-triage" is how AI agents identify this server
server = Server("city-service-triage")


# ── TOOL 1: list_requests ──────────────────────────────────────────
@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Declares all available tools to the AI agent.
    The agent reads these descriptions to decide which tool to call.
    Think of this as the "menu" of available actions.
    """
    return [
        types.Tool(
            name="list_requests",
            description=(
                "Get a list of city service requests. "
                "Optionally filter by category (maintenance, safety, "
                "sanitation, facility, IT), priority (low, medium, high, "
                "critical), or status (open, in_progress, resolved)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {
                        "type": "string",
                        "description": "Filter by category",
                        "enum": ["maintenance", "safety", "sanitation",
                                 "facility", "IT", "general"]
                    },
                    "priority": {
                        "type": "string",
                        "description": "Filter by priority level",
                        "enum": ["low", "medium", "high", "critical"]
                    },
                    "status": {
                        "type": "string",
                        "description": "Filter by current status",
                        "enum": ["open", "in_progress", "resolved"]
                    }
                },
                "required": []
            }
        ),

        types.Tool(
            name="get_request",
            description=(
                "Get a single city service request by its ID number. "
                "Returns all details including category, priority, "
                "status, recommended action, and submission timestamp."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "The unique ID of the service request"
                    }
                },
                "required": ["request_id"]
            }
        ),

        types.Tool(
            name="update_request_status",
            description=(
                "Update the status of a city service request. "
                "Use this when a request has been acted on. "
                "Valid statuses: open, in_progress, resolved."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {
                        "type": "integer",
                        "description": "The ID of the request to update"
                    },
                    "status": {
                        "type": "string",
                        "description": "The new status to set",
                        "enum": ["open", "in_progress", "resolved"]
                    }
                },
                "required": ["request_id", "status"]
            }
        )
    ]


# ── TOOL EXECUTION ─────────────────────────────────────────────────
@server.call_tool()
async def call_tool(
    name: str,
    arguments: dict
) -> list[types.TextContent]:
    """
    Handles all tool calls from the AI agent.
    Routes to the correct API endpoint based on tool name.
    Returns results as text that the AI agent can read.

    Args:
        name: The tool name the agent called (e.g. "list_requests")
        arguments: The parameters the agent passed in

    Returns:
        List of TextContent objects the agent reads as its response
    """
    async with httpx.AsyncClient() as client:

        # ── Tool: list_requests ────────────────────────────────────
        if name == "list_requests":
            # Build query parameters from whatever filters were provided
            # Only include params that were actually passed in
            params = {}
            if arguments.get("category"):
                params["category"] = arguments["category"]
            if arguments.get("priority"):
                params["priority"] = arguments["priority"]
            if arguments.get("status"):
                params["status"] = arguments["status"]

            response = await client.get(
                f"{API_BASE}/requests",
                params=params
            )
            response.raise_for_status()
            requests = response.json()

            if not requests:
                return [types.TextContent(
                    type="text",
                    text="No service requests found matching the criteria."
                )]

            # Format the results as readable text for the AI agent
            lines = [f"Found {len(requests)} service request(s):\n"]
            for r in requests:
                lines.append(
                    f"ID: {r['id']} | "
                    f"Category: {r['category']} | "
                    f"Priority: {r['priority']} | "
                    f"Status: {r['status']}\n"
                    f"Description: {r['description']}\n"
                    f"Location: {r['location']}\n"
                    f"Recommended Action: {r['recommended_action']}\n"
                    f"Submitted: {r['created_at']}\n"
                    f"{'─' * 50}"
                )

            return [types.TextContent(
                type="text",
                text="\n".join(lines)
            )]

        # ── Tool: get_request ──────────────────────────────────────
        elif name == "get_request":
            request_id = arguments["request_id"]

            response = await client.get(
                f"{API_BASE}/requests/{request_id}"
            )

            # Handle 404 gracefully
            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=f"No service request found with ID {request_id}."
                )]

            response.raise_for_status()
            r = response.json()

            result = (
                f"Service Request #{r['id']}\n"
                f"{'=' * 40}\n"
                f"Description:        {r['description']}\n"
                f"Location:           {r['location']}\n"
                f"Category:           {r['category']}\n"
                f"Priority:           {r['priority']}\n"
                f"Status:             {r['status']}\n"
                f"Recommended Action: {r['recommended_action']}\n"
                f"Submitted:          {r['created_at']}\n"
            )

            return [types.TextContent(type="text", text=result)]

        # ── Tool: update_request_status ────────────────────────────
        elif name == "update_request_status":
            request_id = arguments["request_id"]
            status = arguments["status"]

            response = await client.patch(
                f"{API_BASE}/requests/{request_id}/status",
                params={"status": status}
            )

            if response.status_code == 404:
                return [types.TextContent(
                    type="text",
                    text=f"No service request found with ID {request_id}."
                )]

            if response.status_code == 400:
                return [types.TextContent(
                    type="text",
                    text=f"Invalid status value: {status}. "
                         f"Must be: open, in_progress, or resolved."
                )]

            response.raise_for_status()
            r = response.json()

            return [types.TextContent(
                type="text",
                text=(
                    f"Successfully updated Request #{r['id']} "
                    f"status to '{r['status']}'.\n"
                    f"Description: {r['description']}\n"
                    f"Location: {r['location']}"
                )
            )]

        # ── Unknown tool ───────────────────────────────────────────
        else:
            return [types.TextContent(
                type="text",
                text=f"Unknown tool: {name}"
            )]


# ── MAIN ENTRY POINT ───────────────────────────────────────────────
async def main():
    """
    Starts the MCP server using stdio transport.
    stdio means the server communicates through
    standard input/output — the standard for MCP servers.
    AI agents connect by launching this process and
    communicating through stdin/stdout.
    """
    async with stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            server.create_initialization_options()
        )


if __name__ == "__main__":
    asyncio.run(main())
    