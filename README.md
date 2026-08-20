# City Service Triage Agent
### AI-Assisted Service Request Management System
**City of Los Angeles — Department of General Services**
**Agentic Software Engineering Internship Project**

---

## What This Project Does

The City of Los Angeles receives thousands of service requests
every week through unstructured channels. This application provides
an AI-assisted triage workflow that:

- **Classifies** every request automatically into a category
  (maintenance, safety, sanitation, facility, IT)
- **Prioritizes** every request by urgency (low, medium, high, critical)
- **Generates** a recommended next action for every request
- **Displays** all requests in a real-time filterable dashboard
- **Exposes** all data and operations as MCP tools for AI agents
- **Tests** all logic with 17+ pytest unit and integration tests

---

## Quick Start

```bash
# Clone the repo
git clone https://github.com/Kaidena95/city-service-triage-agent.git
cd city-service-triage-agent

# Set up environment
cd backend
python3.11 -m venv venv
source venv/bin/activate
pip install fastapi "uvicorn[standard]" sqlmodel mcp httpx pytest

# Run the server
uvicorn main:app --reload --reload-exclude 'venv/**'

# Open the frontend (in a new terminal)
open ../frontend/index.html
```

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend API | Python + FastAPI |
| Database | SQLite + SQLModel ORM |
| Triage Engine | Rules-based keyword classifier |
| MCP Server | Python MCP SDK |
| Frontend | HTML + CSS + JavaScript |
| Tests | pytest + FastAPI TestClient |

---

## Project Structure

```
city-service-triage-agent/
├── backend/
│   ├── main.py          ← FastAPI app — 6 endpoints + CORS
│   ├── models.py        ← ServiceRequest database table
│   ├── database.py      ← SQLite engine and session
│   ├── schemas.py       ← API input/output contracts
│   ├── triage.py        ← Rules-based classifier + action generator
│   └── tests/
│       ├── test_triage.py   ← 13 classifier unit tests
│       └── test_api.py      ← 18 API integration tests
├── frontend/
│   └── index.html       ← Form + dashboard + filters
├── mcp/
│   ├── service_request_tools.py  ← MCP server (3 tools)
│   └── test_mcp.py               ← MCP simulation tests
└── docs/
    ├── 01_business_statement.md
    ├── 02_logical_structure.md
    ├── 03_technical_implementation_guide.md
    └── 04_agent_regeneration_blueprint.md
```

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Status check |
| POST | `/requests` | Submit + auto-classify a request |
| GET | `/requests` | List all requests (filterable) |
| GET | `/requests/{id}` | Get one request by ID |
| PATCH | `/requests/{id}/status` | Update request status |

### Filter examples

```
GET /requests?category=safety
GET /requests?priority=critical
GET /requests?status=open
GET /requests?category=maintenance&status=open
```

---

## MCP Tools

This app exposes three tools via the Model Context Protocol,
allowing AI agents to interact with service request data:

| Tool | Description |
|------|-------------|
| `list_requests` | Get all requests with optional filters |
| `get_request` | Get one request by ID |
| `update_request_status` | Update a request's status |

### Connect to Claude Desktop

Add to your Claude Desktop MCP config:

```json
{
  "mcpServers": {
    "city-service-triage": {
      "command": "python3",
      "args": ["/path/to/mcp/service_request_tools.py"]
    }
  }
}
```

---

## How the Triage Classifier Works

The classifier uses deterministic keyword matching — no ML model,
no training data, fully explainable and testable.

```
Input: "Broken streetlight near 5th and Main"

Step 1: Lowercase the text
Step 2: Score each category by keyword matches
        maintenance: 2 matches ("broken", "streetlight")
        safety: 0 matches
Step 3: best_category = "maintenance"
Step 4: Score each priority in order [critical, high, medium, low]
        high: 1 match ("broken")
Step 5: best_priority = "high"
Step 6: Look up ACTION_MAP["maintenance"]["high"]

Output:
  category           = "maintenance"
  priority           = "high"
  recommended_action = "Schedule repair crew within 24 hours"
```

Design decision: Deterministic logic is used instead of ML because
every decision is fully traceable, testable with pytest, and
documentable in plain markdown — all three properties required
for this submission's Gemini regeneration test.

---

## Run Tests

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Expected: 17+ tests passed, 0 failed.

---

## Submission Documents

All four required submission documents are in the `docs/` folder:

| Document | Purpose |
|----------|---------|
| `01_business_statement.md` | Problem, solution, business value |
| `02_logical_structure.md` | Architecture, data flow, API contract |
| `03_technical_implementation_guide.md` | Step-by-step build instructions |
| `04_agent_regeneration_blueprint.md` | Machine-readable blueprint for AI regeneration |

The technical guide and regeneration blueprint are written with
enough algorithmic clarity that an AI agent can regenerate the
complete application from the documentation alone.

---

## What I Learned

Building this project taught me:

- How to design and build a REST API with FastAPI from scratch
- How relational databases work and how to use SQLModel as an ORM
- What Model Context Protocol (MCP) is and how to expose app
  functions as tools for AI agents
- How to write deterministic classifiers that are explainable
  and testable — and why that matters more than ML for some problems
- How to document a system precisely enough that an AI can
  reproduce it — a core agentic engineering skill
- How to structure a professional project with tests,
  documentation, and clean git history

---

## Author

**Khader Alakroush**
MSIS Student
GitHub: [@Kaidena95](https://github.com/Kaidena95)

---

*Built as a sample project for the City of Los Angeles*
*Department of General Services — Agentic Software Engineering Internship*
