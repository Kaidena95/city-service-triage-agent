# Week 3 Day 1-2 — MCP Server (Agentic Layer)
## City Service Triage Agent

> **Purpose:** Documents the Model Context Protocol (MCP) server — the agentic layer that exposes app functionality as structured tools an AI agent can call reliably.

---

## What is MCP and Why It Matters

MCP (Model Context Protocol) is a standard protocol that lets AI agents call tools in your application in a structured, reliable way.

### The Problem MCP Solves

```
WITHOUT MCP:
AI Agent wants data → guesses API structure
→ calls wrong endpoints → unreliable results

WITH MCP:
AI Agent calls named tool: list_requests(status="open")
→ gets structured data every time → reliable
```

MCP gives AI agents a formal interface with:
- Named tools with clear descriptions
- Defined input schemas the agent reads
- Predictable structured output every time

### MCP vs REST API

| Aspect | REST API | MCP |
|--------|----------|-----|
| Designed for | Humans and apps | AI agents |
| Discovery | Read documentation | Agent reads tool descriptions |
| Inputs | HTTP methods + JSON | Named parameters with types |
| Reliability | Agent must guess structure | Agent knows exact interface |
| Use case | Frontend, integrations | Agentic workflows |

---

## Three MCP Tools Built

| Tool | What it does | When AI uses it |
|------|-------------|----------------|
| `list_requests` | Get requests with optional filters | "Show me open safety requests" |
| `get_request` | Get one request by ID | "Tell me about request 5" |
| `update_request_status` | Change a request status | "Mark request 3 as resolved" |

---

## Architecture — How MCP Fits In

```
Human  → Browser → Frontend HTML → FastAPI → database.db
                                      ↑
AI Agent → MCP Server ────────────────┘

Both interfaces talk to the same FastAPI endpoints.
MCP server is a thin translation layer — no duplicate logic.
```

Why call FastAPI instead of database directly:
- Business logic stays in one place
- MCP server stays thin
- API validates all inputs — MCP inherits that
- One change in API applies to both human and AI interfaces

---

## Environment Setup

```bash
# Step 1 — go to backend, activate venv
cd ~/Desktop/city-service-triage-agent/backend
source venv/bin/activate

# Step 2 — install MCP library
pip install mcp httpx

# Step 3 — verify installation
pip show mcp

# Step 4 — start FastAPI server in Terminal 1
uvicorn main:app --reload --reload-exclude 'venv/**'
```

Open Terminal 2: `Command + Shift + ` ``

---

## Files Created

### New File — `mcp/service_request_tools.py`

Full MCP server exposing three tools.

**Key structure:**

```python
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

API_BASE = "http://127.0.0.1:8000"
server = Server("city-service-triage")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    """
    Declares available tools to the AI agent.
    Agent reads these descriptions to decide which tool to call.
    """
    return [
        types.Tool(
            name="list_requests",
            description="Get city service requests with optional filters...",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string", "enum": [...]},
                    "priority": {"type": "string", "enum": [...]},
                    "status":   {"type": "string", "enum": [...]}
                },
                "required": []   # all filters optional
            }
        ),
        types.Tool(name="get_request", ...),
        types.Tool(name="update_request_status", ...)
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict):
    """Routes tool calls to the correct FastAPI endpoint."""
    async with httpx.AsyncClient() as client:
        if name == "list_requests":
            params = {}
            if arguments.get("category"): params["category"] = arguments["category"]
            if arguments.get("priority"): params["priority"] = arguments["priority"]
            if arguments.get("status"):   params["status"]   = arguments["status"]
            response = await client.get(f"{API_BASE}/requests", params=params)
            # format and return results as TextContent

        elif name == "get_request":
            response = await client.get(f"{API_BASE}/requests/{arguments['request_id']}")
            # format and return result as TextContent

        elif name == "update_request_status":
            response = await client.patch(
                f"{API_BASE}/requests/{arguments['request_id']}/status",
                params={"status": arguments["status"]}
            )
            # return confirmation as TextContent
```

---

### New File — `mcp/test_mcp.py`

Simulates what an AI agent does when calling your MCP tools.
Run this to verify tools work before connecting a real agent.

```bash
# WHERE: city-service-triage-agent/mcp/  (venv active)
python3 test_mcp.py
```

Tests all three tools:
- list_requests() — all requests
- list_requests(category="safety", priority="critical") — filtered
- get_request(1) — single request detail
- update_request_status(1, "in_progress") — status change
- get_request(1) — confirm status changed

---

## How MCP Tool Call Works Step by Step

```
AI Agent receives prompt:
"Show me all critical safety requests"
        ↓
Agent reads tool descriptions from list_tools()
Decides: list_requests is the right tool
        ↓
Agent calls:
  call_tool("list_requests", {"category": "safety", "priority": "critical"})
        ↓
MCP server call_tool() runs:
  → builds params: {category: "safety", priority: "critical"}
  → sends GET http://127.0.0.1:8000/requests?category=safety&priority=critical
        ↓
FastAPI get_all_requests() runs:
  → applies WHERE category="safety" AND priority="critical"
  → returns matching rows from database.db
        ↓
MCP server formats results as readable text
Returns list[TextContent] to the agent
        ↓
AI Agent reads the text response
Can now answer: "There are 2 critical safety requests: ..."
```

---

## Understanding the inputSchema

The `inputSchema` is a JSON Schema object that tells the AI agent:
- What parameters the tool accepts
- What type each parameter is
- Which parameters are required vs optional
- What values are valid (enum)

```json
{
  "type": "object",
  "properties": {
    "category": {
      "type": "string",
      "description": "Filter by category",
      "enum": ["maintenance", "safety", "sanitation", "facility", "IT"]
    }
  },
  "required": []
}
```

`"required": []` means all parameters are optional.
`"required": ["request_id"]` means request_id must always be provided.

The agent reads this schema and knows exactly how to call the tool.

---

## What is stdio Transport?

MCP servers communicate through standard input/output (stdin/stdout).

```
AI Agent process                MCP Server process
      │                               │
      │── tool call (via stdin) ──→   │
      │                               │ calls FastAPI
      │← text response (stdout) ──    │
```

This means:
- No network port needed for the MCP server itself
- AI agent launches the MCP server as a subprocess
- They communicate directly through process streams
- Simple, fast, no additional config

---

## How to Run the MCP Server

The MCP server runs as a subprocess — you do not start it manually.
An AI agent or MCP client starts it automatically.

To test it manually (simulating an agent):
```bash
# WHERE: city-service-triage-agent/mcp/
cd ~/Desktop/city-service-triage-agent/mcp
source ../backend/venv/bin/activate
python3 test_mcp.py
```

To run the actual MCP server directly (for MCP client connections):
```bash
python3 service_request_tools.py
```

---

## MCP Configuration for AI Clients

To connect this MCP server to Claude Desktop or another MCP client,
add this to the client's config file:

```json
{
  "mcpServers": {
    "city-service-triage": {
      "command": "python3",
      "args": [
        "/Users/yourname/Desktop/city-service-triage-agent/mcp/service_request_tools.py"
      ]
    }
  }
}
```

The AI client then has access to all three tools in every conversation.

---

## Interview Prep

### What problem does MCP solve that REST doesn't?

REST APIs are designed for humans and programmatic clients that know the API structure in advance. An AI agent receiving a natural language prompt ("show me urgent requests") has to guess which endpoint to call, what parameters to send, and how to parse the response.

MCP gives the agent a formal tool menu with named functions, typed parameters, and descriptions written for the agent to read. The agent can reliably select and call the right tool without guessing.

### What is the difference between list_tools() and call_tool()?

`list_tools()` is the discovery function. It returns the tool menu — all available tools with their names, descriptions, and schemas. The agent calls this once on startup to learn what it can do.

`call_tool()` is the execution function. It runs when the agent actually wants to use a tool. It receives the tool name and arguments, executes the logic, and returns the result.

### Why call FastAPI instead of the database directly?

Keeping business logic centralized. If the MCP server queried the database directly, any change to business rules (validation, new fields, classifier updates) would need to be updated in two places. By calling FastAPI, the MCP server inherits all existing validation, error handling, and business logic for free. The MCP layer is purely a translation layer.

### What does required: [] mean in the inputSchema?

It means all parameters are optional. The agent can call the tool with no arguments and get all requests, or provide any combination of filters. If a parameter were in the required array, the agent would be forced to always provide it — calling the tool without it would be a protocol error.

### How does this relate to agentic engineering?

Agentic engineering means building systems that AI agents can operate autonomously — not just answering questions but taking actions. The MCP layer is what makes this app agentic: an AI agent can now query service requests, identify critical ones, and update their status without a human clicking through the dashboard. The agent uses your tools as its hands.

---

## Folder Structure After Week 3 Day 1-2

```
city-service-triage-agent/
├── backend/
│   ├── venv/
│   ├── database.db
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── triage.py
│   └── main.py
├── frontend/
│   └── index.html
├── mcp/
│   ├── service_request_tools.py    ← NEW: MCP server
│   └── test_mcp.py                 ← NEW: tool simulation tests
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   ├── 03_day3_api_endpoints.md
│   ├── 04_day4_frontend.md
│   ├── 05_day5_logical_structure.md
│   ├── 06_week2_triage_classifier.md
│   ├── 07_week2_day3_5_dashboard.md
│   └── 08_week3_mcp_server.md    ← this file
└── .gitignore
```

---

## Git Commit — End of Week 3 Day 1-2

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Week 3 Day 1-2: MCP server with list, get, and update tools"
git push
```

---

## Next Step

→ **Week 3 Day 3:** pytest — write tests for the classifier
and API endpoints so the submission looks credible and production-ready.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Week 3 Day 1-2 — MCP Server*
