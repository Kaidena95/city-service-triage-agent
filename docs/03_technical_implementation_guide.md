# Technical Implementation Guide
## City Service Triage Agent

> This document is written with enough algorithmic clarity
> that an AI agent can regenerate the application from this
> text alone. Every file, field, endpoint, and logic step
> is specified explicitly.

---

## Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Language | Python | 3.11+ |
| API Framework | FastAPI | 0.100+ |
| Server | Uvicorn | 0.20+ |
| ORM | SQLModel | 0.0.14+ |
| Database | SQLite | Built into Python |
| MCP SDK | mcp | 1.0+ |
| HTTP Client | httpx | 0.24+ |
| Testing | pytest | 7.0+ |
| Frontend | HTML + CSS + JavaScript | No framework |

---

## Project Structure

```
city-service-triage-agent/
├── backend/
│   ├── venv/
│   ├── database.db
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── triage.py
│   ├── main.py
│   └── tests/
│       ├── __init__.py
│       ├── test_triage.py
│       └── test_api.py
├── frontend/
│   └── index.html
├── mcp/
│   ├── service_request_tools.py
│   └── test_mcp.py
├── docs/
└── .gitignore
```

---

## Step 1 — Environment Setup

```bash
mkdir city-service-triage-agent
cd city-service-triage-agent
mkdir backend frontend mcp docs

cd backend
python3.11 -m venv venv
source venv/bin/activate

pip install fastapi "uvicorn[standard]" sqlmodel mcp httpx pytest
```

---

## Step 2 — Database Layer

### backend/models.py

Define the ServiceRequest table using SQLModel:

```python
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field

class ServiceRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    location: str
    category: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    status: str = Field(default="open")
    recommended_action: Optional[str] = Field(default=None)
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
```

Field rules:
- id: auto-assigned by SQLite, Optional before save
- description: required string, citizen provides
- location: required string, citizen provides
- category: optional, assigned by classifier
- priority: optional, assigned by classifier
- status: defaults to "open"
- recommended_action: optional, assigned by classifier
- created_at: ISO format UTC string, auto-assigned on creation

### backend/database.py

```python
from sqlmodel import SQLModel, create_engine, Session

DATABASE_URL = "sqlite:///./database.db"

engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)

def create_db_and_tables():
    SQLModel.metadata.create_all(engine)

def get_session():
    with Session(engine) as session:
        yield session
```

---

## Step 3 — Triage Classifier

### backend/triage.py

```python
CATEGORY_KEYWORDS = {
    "safety": [
        "danger","dangerous","emergency","fire","accident",
        "injury","injured","hazard","hazardous","unsafe",
        "gas leak","exposed wire","collapsed","flood"
    ],
    "maintenance": [
        "streetlight","street light","pothole","broken",
        "damaged","repair","road","sidewalk","crack",
        "cracked","fallen","tree","branch","sign",
        "traffic light","signal","bench","fence"
    ],
    "sanitation": [
        "trash","garbage","waste","litter","dumping",
        "illegal dump","smell","sewage","drain","overflow",
        "rodent","rats","pest","dirty","spill"
    ],
    "facility": [
        "park","building","restroom","bathroom","playground",
        "recreation","community center","library","pool",
        "field","court","facility"
    ],
    "IT": [
        "website","portal","system","login","access",
        "password","app","application","online","internet",
        "computer","software","technical","error","bug"
    ]
}

PRIORITY_KEYWORDS = {
    "critical": [
        "emergency","fire","injury","danger","gas leak",
        "collapsed","flood","accident","immediately","urgent","critical"
    ],
    "high": [
        "broken","damaged","unsafe","hazard","blocking",
        "blocked","spill","overflow","illegal dump","crime"
    ],
    "medium": [
        "pothole","crack","graffiti","trash","garbage",
        "rodent","rats","fallen","tree","branch","smell"
    ],
    "low": [
        "park","bench","sign","playground","website",
        "portal","login","password","request","inquiry"
    ]
}

ACTION_MAP = {
    "safety": {
        "critical": "Dispatch emergency response team immediately. Contact 911 if not already done.",
        "high":     "Alert safety department. Schedule on-site inspection within 4 hours.",
        "medium":   "Route to safety department. Schedule inspection within 24 hours.",
        "low":      "Log for safety review. Schedule inspection within 72 hours."
    },
    "maintenance": {
        "critical": "Dispatch repair crew immediately. Block off area if needed.",
        "high":     "Schedule repair crew within 24 hours. Flag as priority work order.",
        "medium":   "Schedule repair crew within 72 hours.",
        "low":      "Add to next scheduled maintenance cycle."
    },
    "sanitation": {
        "critical": "Dispatch sanitation emergency crew immediately.",
        "high":     "Schedule sanitation crew within 24 hours.",
        "medium":   "Route to sanitation department. Schedule within 72 hours.",
        "low":      "Add to next scheduled sanitation route."
    },
    "facility": {
        "critical": "Dispatch facilities emergency team immediately.",
        "high":     "Alert facilities manager. Schedule repair within 24 hours.",
        "medium":   "Route to facilities department. Schedule within one week.",
        "low":      "Log for next scheduled facilities maintenance review."
    },
    "IT": {
        "critical": "Escalate to IT emergency support immediately.",
        "high":     "Route to IT help desk. Priority ticket — respond within 4 hours.",
        "medium":   "Submit IT help desk ticket. Respond within 24 hours.",
        "low":      "Log IT request. Address in next support cycle."
    },
    "general": {
        "critical": "Escalate immediately — review and route to appropriate department.",
        "high":     "Review and route to appropriate department within 4 hours.",
        "medium":   "Review and route to appropriate department within 24 hours.",
        "low":      "Review and route to appropriate department within one week."
    }
}

def classify_request(description: str) -> dict:
    text = description.lower()

    category_scores = {
        cat: sum(1 for kw in kws if kw in text)
        for cat, kws in CATEGORY_KEYWORDS.items()
    }
    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] == 0:
        best_category = "general"

    priority_order = ["critical", "high", "medium", "low"]
    best_priority = "low"
    for p in priority_order:
        if sum(1 for kw in PRIORITY_KEYWORDS[p] if kw in text) > 0:
            best_priority = p
            break

    action_cat = best_category if best_category in ACTION_MAP else "general"
    recommended_action = ACTION_MAP[action_cat][best_priority]

    return {
        "category": best_category,
        "priority": best_priority,
        "recommended_action": recommended_action
    }
```

---

## Step 4 — API Schemas

### backend/schemas.py

```python
from typing import Optional
from sqlmodel import SQLModel

class ServiceRequestCreate(SQLModel):
    description: str
    location: str

class ServiceRequestRead(SQLModel):
    id: int
    description: str
    location: str
    category: Optional[str]
    priority: Optional[str]
    status: str
    recommended_action: Optional[str]
    created_at: str
    model_config = {"from_attributes": True}
```

---

## Step 5 — FastAPI Application

### backend/main.py

```python
from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import ServiceRequest
from schemas import ServiceRequestCreate, ServiceRequestRead
from triage import classify_request

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield

app = FastAPI(lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.post("/requests", response_model=ServiceRequestRead)
def create_request(
    request_data: ServiceRequestCreate,
    session: Session = Depends(get_session)
):
    triage_result = classify_request(request_data.description)
    db_request = ServiceRequest(
        description=request_data.description,
        location=request_data.location,
        category=triage_result["category"],
        priority=triage_result["priority"],
        recommended_action=triage_result["recommended_action"]
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request

@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(
    session: Session = Depends(get_session),
    category: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    query = select(ServiceRequest)
    if category: query = query.where(ServiceRequest.category == category)
    if priority: query = query.where(ServiceRequest.priority == priority)
    if status:   query = query.where(ServiceRequest.status == status)
    return session.exec(query).all()

@app.get("/requests/{request_id}", response_model=ServiceRequestRead)
def get_request(
    request_id: int,
    session: Session = Depends(get_session)
):
    db_request = session.get(ServiceRequest, request_id)
    if not db_request:
        raise HTTPException(
            status_code=404,
            detail=f"Request with id {request_id} not found"
        )
    return db_request

@app.patch("/requests/{request_id}/status")
def update_status(
    request_id: int,
    status: str,
    session: Session = Depends(get_session)
):
    valid = ["open", "in_progress", "resolved"]
    if status not in valid:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid}"
        )
    db_request = session.get(ServiceRequest, request_id)
    if not db_request:
        raise HTTPException(
            status_code=404,
            detail=f"Request with id {request_id} not found"
        )
    db_request.status = status
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request
```

---

## Step 6 — Run the Application

```bash
cd backend
source venv/bin/activate
uvicorn main:app --reload --reload-exclude 'venv/**'
```

Verify at:
- http://127.0.0.1:8000 — health check returns JSON message
- http://127.0.0.1:8000/docs — Swagger UI lists all endpoints

---

## Step 7 — Frontend

### frontend/index.html

Single HTML file. Must contain:

- Form section:
  - textarea id="description" — citizen describes the issue
  - input id="location" — citizen provides location
  - button onclick="submitRequest()" — triggers POST /requests

- Dashboard section:
  - Filter bar with three selects: category, priority, status
  - Clear Filters button that resets all dropdowns
  - Table with columns: id, description, location, category,
    priority, recommended_action, status dropdown, created_at
  - Record count display above the table

- JavaScript functions:
  - submitRequest() — validates fields, POST /requests, refresh dashboard
  - loadRequests(url) — GET /requests, render table rows
  - applyFilters() — build URL with URLSearchParams, call loadRequests
  - clearFilters() — reset all dropdowns, call loadRequests
  - updateStatus(id, status) — PATCH /requests/{id}/status, reapply filters
  - priorityBadge(priority) — return colored span HTML string
  - formatDate(isoString) — format UTC ISO string to readable date

API base URL must be: http://127.0.0.1:8000
CORS middleware must be enabled on the backend.
Status select inside each table row must pre-select current status.

---

## Step 8 — MCP Server

### mcp/service_request_tools.py

```python
import asyncio
import httpx
from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp import types

API_BASE = "http://127.0.0.1:8000"
server = Server("city-service-triage")

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    return [
        types.Tool(
            name="list_requests",
            description="Get city service requests with optional filters.",
            inputSchema={
                "type": "object",
                "properties": {
                    "category": {"type": "string",
                        "enum": ["maintenance","safety","sanitation",
                                 "facility","IT","general"]},
                    "priority": {"type": "string",
                        "enum": ["low","medium","high","critical"]},
                    "status": {"type": "string",
                        "enum": ["open","in_progress","resolved"]}
                },
                "required": []
            }
        ),
        types.Tool(
            name="get_request",
            description="Get a single service request by ID.",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"}
                },
                "required": ["request_id"]
            }
        ),
        types.Tool(
            name="update_request_status",
            description="Update the status of a service request.",
            inputSchema={
                "type": "object",
                "properties": {
                    "request_id": {"type": "integer"},
                    "status": {"type": "string",
                        "enum": ["open","in_progress","resolved"]}
                },
                "required": ["request_id", "status"]
            }
        )
    ]

@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    async with httpx.AsyncClient() as client:
        if name == "list_requests":
            params = {}
            if arguments.get("category"): params["category"] = arguments["category"]
            if arguments.get("priority"): params["priority"] = arguments["priority"]
            if arguments.get("status"):   params["status"]   = arguments["status"]
            response = await client.get(f"{API_BASE}/requests", params=params)
            response.raise_for_status()
            requests = response.json()
            if not requests:
                return [types.TextContent(type="text",
                    text="No service requests found.")]
            lines = [f"Found {len(requests)} request(s):\n"]
            for r in requests:
                lines.append(
                    f"ID:{r['id']} | {r['category']} | "
                    f"{r['priority']} | {r['status']}\n"
                    f"Description: {r['description']}\n"
                    f"Location: {r['location']}\n"
                    f"Action: {r['recommended_action']}\n"
                )
            return [types.TextContent(type="text", text="\n".join(lines))]

        elif name == "get_request":
            response = await client.get(
                f"{API_BASE}/requests/{arguments['request_id']}")
            if response.status_code == 404:
                return [types.TextContent(type="text",
                    text=f"Request {arguments['request_id']} not found.")]
            r = response.json()
            return [types.TextContent(type="text", text=(
                f"Request #{r['id']}\n"
                f"Description: {r['description']}\n"
                f"Location: {r['location']}\n"
                f"Category: {r['category']} | Priority: {r['priority']}\n"
                f"Status: {r['status']}\n"
                f"Action: {r['recommended_action']}\n"
                f"Submitted: {r['created_at']}"
            ))]

        elif name == "update_request_status":
            response = await client.patch(
                f"{API_BASE}/requests/{arguments['request_id']}/status",
                params={"status": arguments["status"]}
            )
            if response.status_code == 404:
                return [types.TextContent(type="text",
                    text=f"Request {arguments['request_id']} not found.")]
            r = response.json()
            return [types.TextContent(type="text",
                text=f"Updated Request #{r['id']} status to '{r['status']}'.")]

        return [types.TextContent(type="text", text=f"Unknown tool: {name}")]

async def main():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream,
            server.create_initialization_options())

if __name__ == "__main__":
    asyncio.run(main())
```

### mcp/test_mcp.py

Smoke test (not a pytest unit test) that exercises the 3 MCP tools
against a live backend. Must:

1. Check GET /health on the running backend before doing anything else;
   exit with an error message if unreachable.
2. Seed one request via POST /requests so the other tools have data.
3. Call list_requests, get_request, and update_request_status in turn.
4. Assert each call returns non-empty TextContent with no unexpected
   "not found" response.
5. Print a final confirmation line if all three succeed.

Run with the backend already running in another terminal:
```bash
python3 mcp/test_mcp.py
```

---

## Step 9 — Tests

```bash
cd backend
mkdir tests
touch tests/__init__.py
```

### backend/tests/test_triage.py

Write 13 unit tests for classify_request():
- test_classify_maintenance_streetlight
- test_classify_maintenance_pothole
- test_classify_safety_emergency
- test_classify_safety_fire
- test_classify_sanitation
- test_classify_facility
- test_classify_it
- test_classify_vague_defaults_to_general
- test_classify_returns_all_fields
- test_classify_priority_values
- test_classify_category_values
- test_classify_case_insensitive
- test_recommended_action_not_empty

### backend/tests/test_api.py

Write 18 integration tests using FastAPI TestClient
with in-memory SQLite database via dependency_overrides.

Use two pytest fixtures:
- session_fixture: creates in-memory SQLite engine and session
- client_fixture: overrides get_session with test session

Tests must cover:
- POST /requests success and auto-classification
- POST /requests with missing fields returns 422
- GET /requests returns list and supports filters
- GET /requests/{id} returns correct record
- GET /requests/999 returns 404
- PATCH status success, invalid status 400, not found 404
- GET / and GET /health return correct responses

Run all tests:
```bash
pytest tests/ -v
```

Minimum required: 17 passed, 0 failed.

---

## Step 10 — Git Setup

```bash
cd city-service-triage-agent
git init
git add .
git commit -m "initial commit: city service triage agent"
git remote add origin https://github.com/USERNAME/city-service-triage-agent.git
git branch -M main
git push -u origin main
```

Daily workflow:
```bash
git add .
git commit -m "describe what you built"
git push
```

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Submission Document 03 — Technical Implementation Guide*
