# Logical Structure Document
## City Service Triage Agent

---

## System Architecture — Three Layers

```
FRONTEND LAYER
frontend/index.html

Technology: HTML + CSS + JavaScript
Serves: Citizens (form) + Staff (dashboard)
Communicates: HTTP fetch() to Backend API

        |
        | HTTP (POST /requests)
        | HTTP (GET /requests)
        | HTTP (PATCH /requests/{id}/status)
        v

BACKEND LAYER
backend/main.py + triage.py + schemas.py

Technology: Python + FastAPI + Uvicorn
Handles: Routing, validation, classification
Communicates: HTTP responses + SQL queries

        |
        | SQL via SQLModel ORM
        v

DATABASE LAYER
backend/database.db + models.py

Technology: SQLite + SQLModel
Stores: All service request records
Accessed by: Backend only

        ^
        | HTTP (internal calls)
        |

MCP LAYER
mcp/service_request_tools.py

Technology: Python + MCP SDK
Exposes: list_requests, get_request, update_request_status
Used by: AI agents via stdio transport
```

---

## Complete Data Flow — Request Submission

```
1. Citizen fills form: description + location
   Clicks "Submit Request"

2. JavaScript fetch() sends:
   POST http://127.0.0.1:8000/requests
   Body: { "description": "...", "location": "..." }

3. FastAPI receives request:
   - CORS middleware allows it
   - Routes to create_request()
   - Validates body against ServiceRequestCreate schema
   - If invalid: returns HTTP 422 automatically

4. create_request() calls classify_request(description):
   - Normalizes text to lowercase
   - Scores each category by keyword matches
   - Picks highest scoring category
   - Scores each priority level
   - Picks highest urgency priority
   - Looks up recommended action from ACTION_MAP
   - Returns: { category, priority, recommended_action }

5. ServiceRequest object built:
   description        = citizen input
   location           = citizen input
   category           = from classifier
   priority           = from classifier
   recommended_action = from classifier
   status             = "open" (default)
   created_at         = UTC timestamp (auto)

6. session.add() then session.commit() writes to database.db
   session.refresh() reloads object to get auto-assigned id

7. FastAPI serializes using ServiceRequestRead schema
   Returns HTTP 200 with full record as JSON

8. JavaScript shows success message
   Calls loadRequests() to refresh dashboard

9. GET /requests fetches all rows (with active filters)
   Dashboard table re-renders with new request visible
```

---

## Triage Classifier Logic

```
Input: description text (string)

Step 1: text = description.lower()

Step 2: For each category in CATEGORY_KEYWORDS:
  score = count of keywords found in text
  category_scores = { maintenance: 2, safety: 0, ... }

Step 3: best_category = category with highest score
  if all scores = 0: best_category = "general"

Step 4: For each priority in ["critical","high","medium","low"]:
  count keywords found in text
  first priority with count > 0 wins
  if none found: priority = "low"

Step 5: recommended_action = ACTION_MAP[best_category][best_priority]

Output: { category, priority, recommended_action }
```

---

## Database Schema

### Table: servicerequest

| Column | Type | Nullable | Default | Set By |
|--------|------|----------|---------|--------|
| id | INTEGER | No | Auto-increment | Database |
| description | TEXT | No | required | Citizen |
| location | TEXT | No | required | Citizen |
| category | TEXT | Yes | NULL | Triage classifier |
| priority | TEXT | Yes | NULL | Triage classifier |
| status | TEXT | No | "open" | System |
| recommended_action | TEXT | Yes | NULL | Triage classifier |
| created_at | TEXT | No | UTC now | System |

### Valid field values

| Field | Values |
|-------|--------|
| category | maintenance, safety, sanitation, facility, IT, general |
| priority | low, medium, high, critical |
| status | open, in_progress, resolved |

---

## API Contract

| Method | Path | Input | Output | Status codes |
|--------|------|-------|--------|-------------|
| GET | / | None | {message} | 200 |
| GET | /health | None | {status: ok} | 200 |
| POST | /requests | {description, location} | ServiceRequestRead | 200, 422 |
| GET | /requests | ?category ?priority ?status | [ServiceRequestRead] | 200 |
| GET | /requests/{id} | path: id | ServiceRequestRead | 200, 404 |
| PATCH | /requests/{id}/status | ?status | ServiceRequestRead | 200, 400, 404 |

---

## MCP Tools Contract

| Tool | Required inputs | Optional inputs | Returns |
|------|----------------|----------------|---------|
| list_requests | none | category, priority, status | Formatted text list |
| get_request | request_id | none | Formatted text detail |
| update_request_status | request_id, status | none | Confirmation text |

---

## File Responsibilities

| File | Layer | Single responsibility |
|------|-------|-----------------------|
| frontend/index.html | Frontend | Form UI, dashboard, fetch calls |
| backend/main.py | Backend | Route definitions, CORS, startup |
| backend/schemas.py | Backend | Input and output data contracts |
| backend/triage.py | Backend | Classification logic only |
| backend/models.py | Database | Table definition |
| backend/database.py | Database | Engine, session, table creation |
| backend/database.db | Database | SQLite binary data file |
| mcp/service_request_tools.py | MCP | Tool definitions and execution |

---

## Why Three Layers Plus MCP?

### Why not let the frontend talk to the database directly?
Security. If the frontend queried the database directly, any user
could run arbitrary queries and read, modify, or delete all data.
The backend is a controlled gateway that validates every request
and enforces business rules.

### Why a separate MCP layer?
The REST API is designed for human-facing frontends.
The MCP layer is designed for AI agents. Having both means
humans use the dashboard while AI agents use structured tools —
each interface optimized for its audience.

### Why SQLite and not PostgreSQL?
SQLite requires zero configuration and ships with Python — perfect
for development. The DATABASE_URL in database.py is the only line
that changes when switching to PostgreSQL in production. SQLModel
abstracts the difference.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Submission Document 02 — Logical Structure*
