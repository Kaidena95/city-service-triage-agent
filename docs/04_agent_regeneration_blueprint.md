# Agent Regeneration Blueprint
## City Service Triage Agent

> This document is a machine-readable blueprint.
> An AI agent following these instructions must be able to
> regenerate the complete application without any other context.

---

## Regeneration Checklist

- [ ] backend/models.py — ServiceRequest SQLModel table
- [ ] backend/database.py — engine, session, create_db_and_tables
- [ ] backend/schemas.py — ServiceRequestCreate, ServiceRequestRead
- [ ] backend/triage.py — classify_request() with keyword maps
- [ ] backend/main.py — FastAPI app with 5 endpoints and CORS
- [ ] frontend/index.html — form, dashboard, filters, JavaScript
- [ ] mcp/service_request_tools.py — MCP server with 3 tools
- [ ] backend/tests/test_triage.py — 13 classifier unit tests
- [ ] backend/tests/test_api.py — 18 API integration tests
- [ ] .gitignore — excludes venv, pycache, .env, .DS_Store

---

## Exact Dependencies

```bash
pip install fastapi "uvicorn[standard]" sqlmodel mcp httpx pytest
```

---

## Exact Database Schema

Table name: servicerequest

| Column | Type | Constraint | Default |
|--------|------|-----------|---------|
| id | INTEGER | PRIMARY KEY AUTOINCREMENT | auto |
| description | TEXT | NOT NULL | required |
| location | TEXT | NOT NULL | required |
| category | TEXT | nullable | NULL |
| priority | TEXT | nullable | NULL |
| status | TEXT | NOT NULL | "open" |
| recommended_action | TEXT | nullable | NULL |
| created_at | TEXT | NOT NULL | UTC ISO string |

---

## Exact Classifier Keyword Lists

```python
CATEGORY_KEYWORDS = {
    "safety": ["danger","dangerous","emergency","fire","accident",
               "injury","injured","hazard","hazardous","unsafe",
               "gas leak","exposed wire","collapsed","flood"],
    "maintenance": ["streetlight","street light","pothole","broken",
                    "damaged","repair","road","sidewalk","crack",
                    "cracked","fallen","tree","branch","sign"],
    "sanitation": ["trash","garbage","waste","litter","dumping",
                   "illegal dump","smell","sewage","drain","overflow",
                   "rodent","rats","pest","dirty","spill"],
    "facility": ["park","building","restroom","bathroom","playground",
                 "recreation","community center","library","pool"],
    "IT": ["website","portal","system","login","access","password",
           "app","application","online","technical","error","bug"]
}

PRIORITY_KEYWORDS = {
    "critical": ["emergency","fire","injury","danger","gas leak",
                 "collapsed","flood","accident","immediately","urgent"],
    "high": ["broken","damaged","unsafe","hazard","blocking",
             "spill","overflow","illegal dump","crime"],
    "medium": ["pothole","crack","graffiti","trash","rodent",
               "rats","fallen","tree","branch","smell"],
    "low": ["park","bench","sign","website","portal",
            "login","password","request","inquiry"]
}
```

---

## Exact Scoring Algorithm

text = description.lower()
For each category: score = count of keywords in text
best_category = argmax(scores)
if all scores = 0: best_category = "general"
For each priority in [critical, high, medium, low]:
if any keyword in text: best_priority = this, break
if no priority matched: best_priority = "low"
recommended_action = ACTION_MAP[best_category][best_priority]
return { category, priority, recommended_action }



---

## Exact API Endpoint Specifications

### POST /requests
- Body: { "description": string, "location": string }
- Calls classify_request(description)
- Creates ServiceRequest with all classifier outputs
- Returns full ServiceRequest record
- Status: 200 success, 422 missing fields

### GET /requests
- Query params all optional: category, priority, status
- Builds SELECT with WHERE clauses for provided params
- Returns array of ServiceRequest records
- Status: 200 always, empty array if no results

### GET /requests/{request_id}
- Path param: request_id integer
- Returns single ServiceRequest record
- Status: 200 found, 404 not found

### PATCH /requests/{request_id}/status
- Path param: request_id integer
- Query param: status string
- Valid values: open, in_progress, resolved
- Updates only the status field
- Status: 200 success, 400 invalid status, 404 not found

---

## Exact MCP Tool Specifications

### list_requests
```json
{
  "name": "list_requests",
  "inputSchema": {
    "type": "object",
    "properties": {
      "category": {"type": "string",
        "enum": ["maintenance","safety","sanitation","facility","IT","general"]},
      "priority": {"type": "string",
        "enum": ["low","medium","high","critical"]},
      "status": {"type": "string",
        "enum": ["open","in_progress","resolved"]}
    },
    "required": []
  }
}
```

### get_request
```json
{
  "name": "get_request",
  "inputSchema": {
    "type": "object",
    "properties": {
      "request_id": {"type": "integer"}
    },
    "required": ["request_id"]
  }
}
```

### update_request_status
```json
{
  "name": "update_request_status",
  "inputSchema": {
    "type": "object",
    "properties": {
      "request_id": {"type": "integer"},
      "status": {"type": "string",
        "enum": ["open","in_progress","resolved"]}
    },
    "required": ["request_id", "status"]
  }
}
```

---

## Verification

After regeneration run:
```bash
cd backend
pytest tests/ -v
```

Required: minimum 17 tests passed, 0 failed.
If any test fails the regeneration is incomplete.

---

## Run Order

cd backend and source venv/bin/activate
uvicorn main:app --reload --reload-exclude 'venv/**'
open frontend/index.html in browser
Submit a test request — verify category and priority assigned
Check dashboard — verify filters work
Run pytest tests/ -v — verify all tests pass
Run python3 mcp/test_mcp.py — verify MCP tools work

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Submission Document 04 — Agent Regeneration Blueprint*