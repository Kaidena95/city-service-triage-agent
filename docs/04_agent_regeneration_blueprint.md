# Agent Regeneration Blueprint
## City Service Triage Agent

> This document is a machine-readable blueprint.
> An AI agent following these instructions must be able to
> regenerate the complete application without any other context.

---

## Regeneration Checklist

An AI regenerating this app must produce all of the following:

- [ ] backend/models.py — ServiceRequest SQLModel table
- [ ] backend/database.py — engine, session, create_db_and_tables
- [ ] backend/schemas.py — ServiceRequestCreate, ServiceRequestRead
- [ ] backend/triage.py — classify_request() with keyword maps
- [ ] backend/main.py — FastAPI app with 5 endpoints and CORS
- [ ] frontend/index.html — form, dashboard, filters, JavaScript
- [ ] mcp/service_request_tools.py — MCP server with 3 tools
- [ ] backend/tests/__init__.py — empty file, makes tests a package
- [ ] backend/tests/test_triage.py — 13 classifier unit tests
- [ ] backend/tests/test_api.py — 18 API integration tests
- [ ] .gitignore — excludes venv, pycache, .env, .DS_Store

---

## Exact Dependencies

Install command:
```bash
pip install fastapi "uvicorn[standard]" sqlmodel mcp httpx pytest
```

| Package | Minimum version |
|---------|----------------|
| fastapi | 0.100.0 |
| uvicorn | 0.20.0 |
| sqlmodel | 0.0.14 |
| mcp | 1.0.0 |
| httpx | 0.24.0 |
| pytest | 7.0.0 |

---

## Exact Database Schema

Table name: servicerequest
(SQLModel lowercases the class name automatically)

```sql
CREATE TABLE servicerequest (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    location TEXT NOT NULL,
    category TEXT,
    priority TEXT,
    status TEXT NOT NULL DEFAULT 'open',
    recommended_action TEXT,
    created_at TEXT NOT NULL
);
```

Field constraints:
- id: auto-incremented integer, never set by user
- description: required, no default
- location: required, no default
- category: nullable, set by classifier after submission
- priority: nullable, set by classifier after submission
- status: not null, defaults to "open"
- recommended_action: nullable, set by classifier after submission
- created_at: not null, ISO 8601 UTC string, set at creation time

---

## Exact Classifier Keyword Lists

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
```

---

## Exact Scoring Algorithm

```
function classify_request(description):

  1. text = description.lower()

  2. For each category in CATEGORY_KEYWORDS:
       score = count of keywords that appear in text
     category_scores = { maintenance: N, safety: N, ... }

  3. best_category = category with highest score
     if all scores equal 0:
       best_category = "general"

  4. priority_order = ["critical", "high", "medium", "low"]
     best_priority = "low"
     for each p in priority_order:
       if any keyword from PRIORITY_KEYWORDS[p] appears in text:
         best_priority = p
         break

  5. if best_category exists in ACTION_MAP:
       action_category = best_category
     else:
       action_category = "general"

  6. recommended_action = ACTION_MAP[action_category][best_priority]

  7. return {
       "category": best_category,
       "priority": best_priority,
       "recommended_action": recommended_action
     }
```

---

## Exact API Endpoint Specifications

### POST /requests
- Method: POST
- Path: /requests
- Request body: { "description": string, "location": string }
- Both fields required — missing field returns HTTP 422
- Calls classify_request(description)
- Builds ServiceRequest with: description, location,
  category, priority, recommended_action from classifier,
  status="open", created_at=datetime.utcnow().isoformat()
- Saves with session.add(), session.commit(), session.refresh()
- Returns: full ServiceRequest record as JSON
- Status codes: 200 success, 422 validation error

### GET /requests
- Method: GET
- Path: /requests
- Query parameters (all optional):
  - category: string
  - priority: string
  - status: string
- Builds SELECT query, adds WHERE clause for each provided param
- Returns: JSON array of ServiceRequest records
- Status codes: 200 always (empty array if no results)

### GET /requests/{request_id}
- Method: GET
- Path: /requests/{request_id}
- Path parameter: request_id integer
- Returns: single ServiceRequest record as JSON
- Status codes: 200 found, 404 not found

### PATCH /requests/{request_id}/status
- Method: PATCH
- Path: /requests/{request_id}/status
- Path parameter: request_id integer
- Query parameter: status string
- Valid status values: open, in_progress, resolved
- Invalid value returns HTTP 400
- Updates only the status field, all other fields unchanged
- Status codes: 200 success, 400 invalid status, 404 not found

### GET /
- Returns: { "message": "City Service Triage API is running" }
- Status: 200

### GET /health
- Returns: { "status": "ok" }
- Status: 200

---

## Exact MCP Tool Specifications

### Tool: list_requests

```json
{
  "name": "list_requests",
  "description": "Get city service requests with optional filters.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "category": {
        "type": "string",
        "enum": ["maintenance","safety","sanitation","facility","IT","general"]
      },
      "priority": {
        "type": "string",
        "enum": ["low","medium","high","critical"]
      },
      "status": {
        "type": "string",
        "enum": ["open","in_progress","resolved"]
      }
    },
    "required": []
  }
}
```

Implementation: GET /requests with provided params as query string.
Returns: formatted text listing all matching requests.

### Tool: get_request

```json
{
  "name": "get_request",
  "description": "Get a single service request by ID.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "request_id": {"type": "integer"}
    },
    "required": ["request_id"]
  }
}
```

Implementation: GET /requests/{request_id}
Returns: formatted text with all request details.

### Tool: update_request_status

```json
{
  "name": "update_request_status",
  "description": "Update the status of a service request.",
  "inputSchema": {
    "type": "object",
    "properties": {
      "request_id": {"type": "integer"},
      "status": {
        "type": "string",
        "enum": ["open","in_progress","resolved"]
      }
    },
    "required": ["request_id", "status"]
  }
}
```

Implementation: PATCH /requests/{request_id}/status?status={status}
Returns: confirmation text with updated request details.

---

## CORS Configuration

Must be added to main.py before any route definitions:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)
```

Without this the browser will block all fetch() calls
from the frontend HTML file.

---

## Test Verification

After regenerating the app run:

```bash
cd backend
source venv/bin/activate
pytest tests/ -v
```

Required result: minimum 17 tests passed, 0 failed.

If any test fails the regeneration is incomplete or incorrect.
Fix the failing component and re-run until all tests pass.

---

## Exact Run Order for Verification

```
1. cd backend
2. source venv/bin/activate
3. uvicorn main:app --reload --reload-exclude 'venv/**'
4. Confirm: INFO: Application startup complete.
5. Open http://127.0.0.1:8000 — verify JSON health message
6. Open http://127.0.0.1:8000/docs — verify all endpoints listed
7. Open frontend/index.html in browser
8. Submit a test request with description containing "broken streetlight"
9. Verify response shows category=maintenance and priority=high
10. Verify dashboard table shows the new row with badges
11. Change status dropdown — verify it updates
12. Run pytest tests/ -v — verify minimum 17 passed
13. Run python3 mcp/test_mcp.py — verify all MCP tools complete
```

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Submission Document 04 — Agent Regeneration Blueprint*
