# Day 5 — Logical Structure Document
## City Service Triage Agent

> **Submission Document 02 — Logical Structure**
> This document serves as both the Week 1 buffer review and the required architectural overview for the internship submission packet.

---

## Business Context

The City of Los Angeles receives service requests across dozens of channels — phone, email, walk-in, web portals — making consistent classification, prioritization, and routing difficult. This application provides an AI-assisted triage workflow that standardizes intake, assigns priority automatically, stores request history, and gives staff a real-time dashboard to monitor pending issues.

---

## System Overview

The City Service Triage Agent is a three-layer web application:

```
┌─────────────────────────────────────────────┐
│              FRONTEND LAYER                  │
│         frontend/index.html                  │
│                                             │
│  What it does: Shows UI to the user        │
│  Technology: HTML + CSS + JavaScript        │
│  Talks to: Backend via HTTP fetch() calls   │
└──────────────────┬──────────────────────────┘
                   │ HTTP (POST /requests)
                   │ HTTP (GET /requests)
                   ▼
┌─────────────────────────────────────────────┐
│              BACKEND LAYER                   │
│    backend/main.py + backend/schemas.py      │
│                                             │
│  What it does: Handles all business logic   │
│  Technology: Python + FastAPI               │
│  Talks to: Frontend (HTTP) + DB (SQLModel)  │
└──────────────────┬──────────────────────────┘
                   │ SQL via SQLModel ORM
                   ▼
┌─────────────────────────────────────────────┐
│              DATABASE LAYER                  │
│  backend/database.db + backend/models.py     │
│                                             │
│  What it does: Stores all data permanently  │
│  Technology: SQLite + SQLModel              │
│  Talks to: Backend only (never frontend)    │
└─────────────────────────────────────────────┘
```

---

## Why Three Layers?

Each layer has one job and one job only. This separation is called **Separation of Concerns** and it is a core software engineering principle.

| If you mixed layers | What would break |
|--------------------|-----------------|
| Frontend talks directly to DB | Any user could read or delete all data |
| Backend contains UI code | Impossible to update UI without touching business logic |
| One giant file for everything | Untestable, unmaintainable, impossible to scale |

The backend is the only layer that touches the database. The frontend only talks to the backend. This means you can swap out any layer independently — for example, replace the HTML frontend with a React app, or replace SQLite with PostgreSQL — without touching the other layers.

---

## Full Data Flow — Service Request Submission

```
CITIZEN ACTION
Fills out form: description + location
Clicks "Submit Request"
        │
        ▼
FRONTEND (index.html)
JavaScript validates: both fields filled?
  → No: shows "Please fill in both fields" error, stops
  → Yes: continues
JavaScript fetch() sends:
  HTTP POST to http://127.0.0.1:8000/requests
  Headers: { Content-Type: application/json }
  Body: { "description": "...", "location": "..." }
        │
        ▼
BACKEND (main.py)
CORS middleware checks request origin → allows it
FastAPI routes POST /requests → create_request()
FastAPI validates body against ServiceRequestCreate schema
  → Missing field: returns HTTP 422 automatically
  → Valid: continues
Depends(get_session) opens database session
create_request() builds ServiceRequest object:
  description = from request body
  location    = from request body
  category    = None  (triage not wired yet — Week 2)
  priority    = None  (triage not wired yet — Week 2)
  status      = "open"
  created_at  = current UTC timestamp
        │
        ▼
DATABASE (database.db)
session.add() stages the object
session.commit() writes row to servicerequest table
session.refresh() reloads object to get auto-assigned id
        │
        ▼
BACKEND (main.py)
FastAPI serializes object using ServiceRequestRead schema
Returns HTTP 200 with full record as JSON:
  { id, description, location, category,
    priority, status, created_at }
        │
        ▼
FRONTEND (index.html)
JavaScript receives response
Shows: "Request #X submitted successfully"
Clears form fields
Calls loadRequests() to refresh dashboard
        │
        ▼
FRONTEND (index.html)
fetch() sends GET /requests
        │
        ▼
BACKEND (main.py)
Queries all rows from servicerequest table
Returns JSON array of all requests
        │
        ▼
FRONTEND (index.html)
Builds HTML table rows from response array
Dashboard updates — new request visible
```

---

## What Each File Does

| File | Layer | Responsibility |
|------|-------|---------------|
| `frontend/index.html` | Frontend | Form UI, dashboard table, JavaScript fetch calls |
| `backend/main.py` | Backend | API route definitions, CORS, startup lifespan |
| `backend/schemas.py` | Backend | Input schema (what API accepts) and output schema (what API returns) |
| `backend/models.py` | Database | ServiceRequest table definition and field types |
| `backend/database.py` | Database | Engine (DB connection), session (per-request transaction), table creation |
| `backend/database.db` | Database | The actual SQLite binary file — all data lives here |

---

## Database Schema

### Table: `servicerequest`

| Column | Type | Nullable | Default | Set By |
|--------|------|----------|---------|--------|
| `id` | INTEGER | No | Auto-increment | Database |
| `description` | TEXT | No | — | Citizen |
| `location` | TEXT | No | — | Citizen |
| `category` | TEXT | Yes | NULL | Triage classifier (Week 2) |
| `priority` | TEXT | Yes | NULL | Triage classifier (Week 2) |
| `status` | TEXT | No | "open" | System |
| `created_at` | TEXT | No | UTC now | System |

### Field value options

| Field | Possible values |
|-------|----------------|
| `category` | maintenance, safety, sanitation, facility, IT |
| `priority` | low, medium, high, critical |
| `status` | open, in_progress, resolved |

---

## API Endpoints

| Method | Path | Input | Output | Purpose |
|--------|------|-------|--------|---------|
| GET | `/` | None | `{"message": "..."}` | Health check |
| GET | `/health` | None | `{"status": "ok"}` | Health check |
| POST | `/requests` | `{description, location}` | Full ServiceRequest | Create new request |
| GET | `/requests` | None | Array of ServiceRequests | List all requests |
| GET | `/requests/{id}` | Path param: id | Single ServiceRequest | Get one request |

### HTTP Status Codes

| Code | Meaning | When it occurs |
|------|---------|---------------|
| 200 | OK | Successful GET or POST |
| 404 | Not Found | Request ID does not exist |
| 422 | Unprocessable Entity | Required field missing in body |

---

## Technology Stack

| Layer | Technology | Why chosen |
|-------|-----------|-----------|
| Frontend | HTML + CSS + JavaScript | Simple, no build step, demonstrates fundamentals |
| API Framework | FastAPI (Python) | Auto-generates docs, fast, type-safe, async-ready |
| ORM | SQLModel | Combines Pydantic + SQLAlchemy, works natively with FastAPI |
| Database | SQLite | File-based, zero config, perfect for development |
| Server | Uvicorn | ASGI server required by FastAPI, production-grade |

---

## Planned Architecture — Weeks 2 and 3

### Week 2 Addition — Triage Layer

```
POST /requests receives description
        ↓
triage.py classify(description)
        ↓
Returns: category + priority
        ↓
Stored in database alongside request
        ↓
Dashboard shows category and priority columns populated
```

New file: `backend/triage.py`
Method: Rules-based keyword matching (deterministic, fully explainable)

Why deterministic over ML:
- Every decision can be documented in plain text
- Fully testable with pytest
- The Gemini regeneration test requires logic that can be expressed in markdown
- Explainable in a technical interview without requiring model weights

---

### Week 3 Addition — MCP Layer

```
AI Agent (LLM)
        ↓
MCP Protocol call
        ↓
mcp/service_request_tools.py
        ↓
Tools: list_requests | get_request | update_request_status
        ↓
Queries/updates database.db
        ↓
Returns structured response to AI agent
```

New file: `mcp/service_request_tools.py`

MCP (Model Context Protocol) is a standard that lets LLMs call tools in your application in a structured way. Instead of an LLM guessing how to call your API, MCP gives it a formal interface with defined inputs and outputs — like a typed API contract for AI agents.

---

## Week 1 Complete File Structure

```
city-service-triage-agent/
├── backend/
│   ├── venv/               ← isolated Python packages
│   ├── database.db         ← SQLite database file
│   ├── database.py         ← engine + session + table creation
│   ├── models.py           ← ServiceRequest table definition
│   ├── schemas.py          ← API input/output schemas
│   └── main.py             ← FastAPI routes + CORS + lifespan
├── frontend/
│   └── index.html          ← form + dashboard + JavaScript
├── mcp/                    ← placeholder (Week 3)
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   ├── 03_day3_api_endpoints.md
│   ├── 04_day4_frontend.md
│   └── 05_day5_logical_structure.md
└── .gitignore
```

---

## Interview Prep — Architecture Questions

### Why does the frontend not talk to the database directly?
Security and maintainability. If the frontend could query the database directly, any user could run arbitrary queries — reading, modifying, or deleting all data. The backend acts as a controlled gateway: it validates every request, enforces business rules, and controls exactly what data is exposed.

### What would break if you removed schemas.py?
You would lose control over what data comes in and what goes out. The database model `ServiceRequest` has fields like `id`, `category`, `priority` that users should never set directly. Without separate schemas, a user could POST `{"id": 1, "status": "resolved"}` and bypass the triage classifier entirely.

### Why SQLite for development, and what would you use in production?
SQLite is a file-based database — zero configuration, no server, ships with Python. Perfect for development and small apps. In production for a city-scale system, PostgreSQL would be the right choice: it supports concurrent users, has robust backup and recovery, and handles large datasets efficiently. Switching from SQLite to PostgreSQL in this app requires changing one line — the `DATABASE_URL` in `database.py` — because SQLModel abstracts the database-specific SQL.

### What is the difference between an engine and a session?
The engine is the permanent infrastructure — the road between your app and the database file, created once when the app starts. The session is a temporary transaction on that road — opened for each incoming request, used to read or write data, then closed automatically. Many sessions run over the lifetime of one engine.

### What does CORS do?
Cross-Origin Resource Sharing is a browser security mechanism. Browsers block JavaScript on one origin (like an HTML file) from calling an API on a different origin (like port 8000) by default. Adding CORS middleware to FastAPI tells the browser explicitly that cross-origin requests are permitted. Without it, every fetch() call from the frontend silently fails.

---

## Git Commit — End of Day 5 / End of Week 1

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Week 1 complete: logical structure doc, full stack working end to end"
git push
```

---

## Week 1 Completion Checklist

- [ ] FastAPI server runs without errors
- [ ] POST /requests creates and stores a request
- [ ] GET /requests returns all requests
- [ ] GET /requests/{id} returns one request or 404
- [ ] Frontend form submits successfully
- [ ] Dashboard loads and displays existing requests
- [ ] database.db has rows visible in SQLite Viewer
- [ ] All five documentation files in docs/ folder
- [ ] Everything pushed to GitHub

---

## Next Step

→ **Week 2 Day 1:** Build the rules-based triage classifier in `backend/triage.py`

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Day 5 — Logical Structure Document + Week 1 Complete*
