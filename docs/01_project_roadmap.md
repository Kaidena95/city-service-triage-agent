# Project Roadmap — 3-Week Training Plan
## City Service Triage Agent

> **Purpose:** Full week-by-week, day-by-day plan for building the City Service Triage Agent.
> Each day includes what to learn, what to build, and who does what (you vs AI-assisted).

---

## Overview

| Week | Focus | Goal |
|------|-------|------|
| Week 1 | Core App | FastAPI + SQLite + simple form working end to end |
| Week 2 | Triage Logic | AI agent layer — classifier, priority, recommended actions |
| Week 3 | MCP + Docs + Tests | Agentic tools, documentation, submission packet |

---

## Week 1 — Core App (FastAPI + SQLite + Simple Form)

### Day 1 — Python Web & API Fundamentals ✅ COMPLETE

**What to learn:**
- What an API actually is and how HTTP works
- HTTP verbs: GET, POST, PUT, DELETE
- What JSON is and why APIs use it
- What FastAPI does for you vs plain Python
- What Uvicorn is and why you need it

**What to build:**
- Project folder structure
- Python virtual environment
- FastAPI "hello world" with two endpoints: `/` and `/health`
- GitHub repository connected and first commit pushed

**Key concepts to understand:**
- `@app.get("/")` — what a decorator is and what it does
- The difference between `/` (raw JSON) and `/docs` (Swagger UI)
- What `--reload` does and why it is development-only
- Why virtual environments exist

**Status:** ✅ Done — server running, pushed to GitHub

---

### Day 2 — Database Basics

**What to learn:**
- What a relational database is (tables, rows, columns, relationships)
- What SQLite is — a file-based database, no server needed, perfect for development
- What SQLModel is — a library that lets you define database tables as Python classes
- What an ORM is (Object Relational Mapper) — maps Python objects to database rows

**What to build:**
- Install SQLModel
- Define the `ServiceRequest` table with all fields
- Connect the database to FastAPI so it creates the table on startup

**The ServiceRequest Table:**

| Field | Type | Purpose |
|-------|------|---------|
| `id` | Integer | Unique identifier, auto-incremented |
| `description` | String | What the citizen reported |
| `location` | String | Where the issue is |
| `category` | String | Type of issue (maintenance, safety, etc.) |
| `priority` | String | How urgent (low, medium, high, critical) |
| `status` | String | Current state (open, in_progress, resolved) |
| `created_at` | DateTime | When the request was submitted |

**Your job after AI generates the model:**
Trace through each field and write in your own words why it exists and what data goes in it.

---

### Day 3 — Build the API Endpoints

**What to learn:**
- How POST vs GET endpoints work differently
- What a request body is and how FastAPI validates it automatically
- What a path parameter is (e.g. `/requests/{id}`)
- How to test endpoints using the `/docs` Swagger UI

**What to build:**

| Endpoint | Method | What it does |
|----------|--------|-------------|
| `/requests` | POST | Accept a new service request and store it in the DB |
| `/requests` | GET | Return a list of all service requests |
| `/requests/{id}` | GET | Return one specific request by its ID |

**Your job after AI generates the endpoints:**
Test each one in `/docs` and write in your own words what happens when you call it — what goes in, what comes out, what status code you get.

---

### Day 4 — Simple Frontend

**What to learn:**
- How a browser sends an HTTP request to your API
- What `fetch()` does in JavaScript
- How HTML forms work and how to connect them to an API call

**What to build:**
- A simple HTML page with a form containing:
  - Description field (text area)
  - Location field (text input)
  - Urgency selector (dropdown)
  - Submit button that POSTs to `/requests`
- A basic list view that GETs from `/requests` and displays them

**Note:** UI polish is not the focus here. A working form that talks to your API is the goal.

---

### Day 5 — Buffer + Begin Logical Structure Doc

**What to do:**
- Catch up on anything from Days 1-4 that needs finishing
- Write the first half of `02_logical_structure.md` while everything is fresh
- Document the architecture you just built: frontend → API → database

**Questions to answer in the doc:**
- What does each layer do?
- How does data flow from the form submission to the database?
- What happens step by step when a user submits a request?

---

## Week 2 — Triage Logic (The AI Agent Layer)

### Day 1-2 — Rules-Based Classifier

**What to learn:**
- Why a deterministic (rules-based) classifier is the right choice here
- What keyword/heuristic matching is
- Why explainability matters more than complexity for this submission
- How to write a function that takes text input and returns a category + priority

**What to build:**
A triage function that:
1. Takes the description text as input
2. Scans for keywords
3. Returns a category and priority

**Categories:**

| Category | Example keywords |
|----------|----------------|
| `maintenance` | streetlight, pothole, broken, repair, road |
| `safety` | danger, accident, hazard, fire, emergency |
| `sanitation` | trash, garbage, waste, graffiti, illegal dumping |
| `facility` | park, building, restroom, playground |
| `IT` | website, system, portal, login, access |

**Priority logic:**

| Priority | When assigned |
|----------|--------------|
| `critical` | Safety keywords detected |
| `high` | Multiple issue keywords or urgent language |
| `medium` | Single clear category match |
| `low` | Vague or unclear description |

**Your job after AI generates the classifier:**
Run at least 5 test cases through it by hand. Write what input you gave, what category came out, what priority came out, and whether it was correct.

**Why deterministic over ML:**
- You can explain every decision in your documentation
- It is fully testable with pytest
- The Gemini regeneration test requires clear logic in your docs — ML weights can't be documented in markdown
- You can still mention "this classifier could be replaced with an LLM call" as a future improvement

---

### Day 3 — Wire Classifier into the POST Endpoint

**What to learn:**
- How to call one Python function from inside a FastAPI endpoint
- How to store the classifier output alongside the user input in the database

**What to build:**
Update the `POST /requests` endpoint so that when a request comes in:
1. It runs the description through the triage classifier
2. Gets back a category and priority automatically
3. Stores everything (user input + classified fields) in one database row

The user submits: description + location
The system adds: category + priority + status (open) + created_at (now)

---

### Day 4 — Recommended Next Action Generator

**What to learn:**
- Template-based logic — how to map a category/priority combination to a predefined action string
- Why this is a valid "agentic" output even without an LLM

**What to build:**
A function that takes category + priority and returns a recommended action string.

Examples:

| Category | Priority | Recommended Action |
|----------|----------|--------------------|
| safety | critical | Dispatch emergency response team immediately |
| maintenance | high | Schedule repair crew within 24 hours |
| sanitation | medium | Route to sanitation department, schedule within 72 hours |
| facility | low | Log for next scheduled maintenance review |

Add a `recommended_action` field to the API response.

---

### Day 5 — Dashboard View

**What to learn:**
- How query parameters work in GET endpoints (e.g. `/requests?category=safety&status=open`)
- How to filter database results in SQLModel

**What to build:**
- Update `GET /requests` to accept optional filter parameters: category, priority, status
- Update the frontend to show a simple dashboard table with those filters as dropdowns

---

## Week 3 — MCP Layer + Documentation + Tests

### Day 1-2 — MCP Server

**What to learn:**
- What MCP (Model Context Protocol) is: a standard way for LLMs to call tools in your application
- What a "tool" is in MCP terms: a named function with defined inputs and outputs that an AI can call
- How to use the `mcp` Python SDK to expose your app's functions as tools

**What to build:**
A minimal MCP server in `mcp/service_request_tools.py` exposing these tools:

| Tool name | What it does |
|-----------|-------------|
| `list_requests` | Returns all service requests, with optional filters |
| `get_request` | Returns one request by ID |
| `update_request_status` | Updates the status field of a request |

**Why this matters for the internship:**
The job title is Agentic Software Engineering. MCP is the protocol that lets an AI agent interact with your application's data. This is the most directly relevant technical component to the role.

---

### Day 3 — Tests with pytest

**What to learn:**
- What pytest is and why tests matter
- How to write a test function
- How to test a FastAPI endpoint using TestClient

**What to build:**
- At least 2 tests for the classifier function (known input → expected output)
- At least 1 test for the POST endpoint (submit a request, verify it is stored)
- At least 1 test for the GET endpoint (retrieve requests, verify response shape)

---

### Day 4 — Write the Four Submission Documents

**What to produce:**

| File | Purpose |
|------|---------|
| `01_business_statement.md` | Problem, solution, business value |
| `02_logical_structure.md` | Architecture, data flow diagram, system design |
| `03_technical_implementation_guide.md` | Step-by-step build instructions precise enough for Gemini to regenerate the app |
| `04_agent_regeneration_blueprint.md` | Explicit file structure, schema, endpoints, tool definitions |

**Your job on these docs:**
AI drafts them. You review every line and add the business reasoning in your own words. You will be asked to defend these in the technical interview.

---

### Day 5 — Dry-Run Regeneration Test

**What to do:**
1. Take `03_technical_implementation_guide.md`
2. Paste it into a fresh Claude or Gemini chat with the prompt: "Regenerate this application from the documentation below"
3. Compare what it produces to your actual code
4. Identify any gaps in the documentation and fix them
5. This is exactly what the internship team will do — you want to pass this test before they run it

---

## Git Commit Schedule

Run these three commands at the end of every day:

```bash
git add .
git commit -m "Day X: one line describing what you built"
git push
```

Suggested commit messages:

| Day | Commit message |
|-----|---------------|
| Week 1 Day 1 | `Day 1: project structure, FastAPI hello world, environment setup` |
| Week 1 Day 2 | `Day 2: SQLModel database, ServiceRequest table defined` |
| Week 1 Day 3 | `Day 3: POST and GET endpoints for service requests` |
| Week 1 Day 4 | `Day 4: HTML frontend form connected to API` |
| Week 1 Day 5 | `Day 5: logical structure doc first draft` |
| Week 2 Day 1 | `Week 2 Day 1: rules-based triage classifier` |
| Week 2 Day 3 | `Week 2 Day 3: classifier wired into POST endpoint` |
| Week 2 Day 4 | `Week 2 Day 4: recommended action generator` |
| Week 2 Day 5 | `Week 2 Day 5: dashboard with filters` |
| Week 3 Day 1 | `Week 3 Day 1: MCP server with list and get tools` |
| Week 3 Day 3 | `Week 3 Day 3: pytest tests for classifier and endpoints` |
| Week 3 Day 4 | `Week 3 Day 4: all four submission markdown docs complete` |
| Week 3 Day 5 | `Week 3 Day 5: dry-run tested, docs finalized, submission ready` |

---

## Final Submission Folder Structure

```
city-service-triage-agent/
├── docs/
│   ├── 00_dev_environment_setup.md     ← setup walkthrough (done)
│   ├── 01_project_roadmap.md           ← this file
│   ├── 02_business_statement.md        ← Week 3 Day 4
│   ├── 03_logical_structure.md         ← Week 1 Day 5 + Week 3 Day 4
│   ├── 04_technical_implementation_guide.md   ← Week 3 Day 4
│   └── 05_agent_regeneration_blueprint.md     ← Week 3 Day 5
├── backend/
│   ├── main.py                         ← FastAPI app
│   ├── database.py                     ← DB connection
│   ├── models.py                       ← ServiceRequest table
│   ├── triage.py                       ← classifier + action generator
│   └── tests/
│       └── test_api.py
├── frontend/
│   └── index.html
├── mcp/
│   └── service_request_tools.py
├── .gitignore
└── README.md
```

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Document: Project Roadmap — 3-Week Training Plan*
