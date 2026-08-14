# Week 2 Day 3-5 — Dashboard Filters, Status Updates & Recommended Actions
## City Service Triage Agent

> **Purpose:** Documents the complete frontend dashboard upgrade — adding category/priority display, recommended actions, live status updates, and filter controls.

---

## What Was Built

| Feature | Where | What it does |
|---------|-------|-------------|
| Category badges | Dashboard table | Color-coded label per request |
| Priority badges | Dashboard table | Color-coded urgency level |
| Recommended action | Dashboard table | Plain-text next step per request |
| Status dropdown | Dashboard table | Staff can update status live |
| Filter bar | Above dashboard | Filter by category, priority, status |
| Combined filters | Filter bar | Multiple filters applied together |
| Record count | Above table | Shows how many results match |

---

## Core Concepts

### What is a Query Parameter?

Extra information added to a URL after a `?` to filter or modify the response:

```
GET /requests                          → all requests
GET /requests?category=maintenance     → only maintenance
GET /requests?priority=high            → only high priority
GET /requests?status=open              → only open
GET /requests?category=safety&status=open → combined
```

Query parameters are optional — the endpoint works with or without them.

Contrast with path parameters which are part of the URL itself:
```
GET /requests/5       → path parameter (required, identifies one record)
GET /requests?id=5    → query parameter (optional filter)
```

---

### Why Filters Matter for the Business Case

A raw list of 500 requests is useless to a city department manager.
Filters provide operational efficiency:

| Who uses it | Filter they need | Why |
|-------------|-----------------|-----|
| Safety department | category=safety | See only their requests |
| Morning supervisor | priority=critical | Triage emergencies first |
| Staff member | status=open | See what still needs work |
| Department head | category=maintenance&status=open | Pending maintenance only |

This is the core business value — faster routing, reduced manual review time, better operational decision-making. Document this in your business statement.

---

### What is a PATCH Request?

`PATCH` updates only specific fields of a record.
`PUT` replaces the entire record — all fields required.

For status updates, `PATCH` is correct:
```
PATCH /requests/1/status?status=in_progress
→ only status changes
→ description, location, category, priority unchanged
```

If we used `PUT`, the frontend would have to send all fields just to change one — wasteful and error-prone.

---

### How URLSearchParams Works

Instead of building URL strings manually:
```javascript
// Bad — error-prone string building
const url = "/requests?category=" + cat + "&priority=" + pri;

// Good — URLSearchParams handles encoding automatically
const params = new URLSearchParams();
if (category) params.append("category", category);
if (priority) params.append("priority", priority);
const url = `/requests?${params.toString()}`;
```

`URLSearchParams` also handles special characters, spaces, and encoding automatically. A description with `&` in it would break a manually built URL.

---

## Environment Setup

```bash
# Step 1 — go to root
cd ~/Desktop/city-service-triage-agent

# Step 2 — go into backend
cd backend

# Step 3 — activate venv (Mac)
source venv/bin/activate

# Step 4 — verify all files present
ls
```

Expected:
```
__pycache__  database.db  database.py
main.py  models.py  schemas.py  triage.py  venv
```

```bash
# Step 5 — start server in Terminal 1
uvicorn main:app --reload --reload-exclude 'venv/**'
```

Open Terminal 2: `Command + Shift + ` ``

---

## Files Updated

### Updated — `backend/main.py`

Key change — GET /requests now accepts optional filters:

```python
from typing import Optional
from fastapi import Query

@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(
    session: Session = Depends(get_session),
    category: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    query = select(ServiceRequest)

    if category:
        query = query.where(ServiceRequest.category == category)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if status:
        query = query.where(ServiceRequest.status == status)

    requests = session.exec(query).all()
    return requests
```

How the filtering works:
1. Start with a query that selects all rows
2. If category filter provided, add a WHERE clause
3. If priority filter provided, add another WHERE clause
4. If status filter provided, add another WHERE clause
5. Each additional WHERE clause narrows the results further

---

### Updated — `frontend/index.html`

Three major additions:

**1 — Filter bar above the dashboard:**
```html
<div class="filter-bar">
  <select id="filter-category" onchange="applyFilters()">
    <option value="">All Categories</option>
    <option value="safety">Safety</option>
    <option value="maintenance">Maintenance</option>
    ...
  </select>
  <button onclick="clearFilters()">Clear Filters</button>
</div>
```

**2 — Status dropdown inside each table row:**
```html
<select onchange="updateStatus(${r.id}, this.value)">
  <option value="open"        ${r.status === "open" ? "selected" : ""}>Open</option>
  <option value="in_progress" ${r.status === "in_progress" ? "selected" : ""}>In Progress</option>
  <option value="resolved"    ${r.status === "resolved" ? "selected" : ""}>Resolved</option>
</select>
```

The `selected` attribute pre-selects the current status so staff see the current state.

**3 — JavaScript filter and status functions:**
```javascript
async function applyFilters() {
    const category = document.getElementById("filter-category").value;
    const priority = document.getElementById("filter-priority").value;
    const status   = document.getElementById("filter-status").value;

    const params = new URLSearchParams();
    if (category) params.append("category", category);
    if (priority) params.append("priority", priority);
    if (status)   params.append("status", status);

    const url = `${API}/requests${params.toString() ? "?" + params.toString() : ""}`;
    await loadRequests(url);
}

async function updateStatus(requestId, newStatus) {
    await fetch(`${API}/requests/${requestId}/status?status=${newStatus}`, {
        method: "PATCH"
    });
    applyFilters(); // reload with current filters still active
}
```

---

## Data Flow — Status Update

```
Staff clicks status dropdown in table row
        ↓
onchange calls updateStatus(requestId, newStatus)
        ↓
JavaScript sends:
  PATCH http://127.0.0.1:8000/requests/1/status?status=in_progress
        ↓
FastAPI update_status() runs:
  → validates status is one of: open, in_progress, resolved
  → fetches row from database by id
  → sets db_request.status = "in_progress"
  → session.commit() writes to database.db
        ↓
FastAPI returns updated record
        ↓
JavaScript calls applyFilters()
        ↓
Dashboard reloads with current filters still active
        ↓
Updated row shows new status
```

---

## Data Flow — Filtering

```
Staff selects "Maintenance" from category dropdown
        ↓
onchange calls applyFilters()
        ↓
JavaScript builds URL:
  http://127.0.0.1:8000/requests?category=maintenance
        ↓
FastAPI get_all_requests() runs:
  → category="maintenance" received from Query param
  → query = select(ServiceRequest)
  → query = query.where(category == "maintenance")
  → session.exec(query).all() returns filtered rows
        ↓
FastAPI returns JSON array of only maintenance requests
        ↓
Dashboard table re-renders with filtered results
Record count shows: "Showing 3 requests"
```

---

## Testing Checklist

| Test | Action | Expected result |
|------|--------|----------------|
| Maintenance submit | Description with "broken streetlight" | category=maintenance, priority=high |
| Safety submit | Description with "gas leak emergency" | category=safety, priority=critical |
| Category filter | Select Maintenance | Only maintenance rows visible |
| Priority filter | Select Critical | Only critical rows visible |
| Combined filter | Safety + Open | Only open safety requests |
| Clear filters | Click Clear Filters | All requests return |
| Status update | Change dropdown to In Progress | Row updates, stays visible |
| Record count | Apply any filter | Count updates to match results |

---

## API Endpoints — Full List After Week 2

| Method | Path | Query Params | Purpose |
|--------|------|-------------|---------|
| GET | `/` | None | Health check |
| GET | `/health` | None | Health check |
| POST | `/requests` | None | Create + auto-classify request |
| GET | `/requests` | category, priority, status | List with optional filters |
| GET | `/requests/{id}` | None | Get one request |
| PATCH | `/requests/{id}/status` | status | Update status only |

---

## Interview Prep

### What is a query parameter vs a path parameter?

Path parameter: part of the URL structure, required, identifies a specific resource.
Example: `/requests/5` — the `5` identifies which request.

Query parameter: added after `?`, optional, modifies the response.
Example: `/requests?category=safety` — the `category` filters the results.

Rule of thumb: use path params to identify, use query params to filter or modify.

### Why call applyFilters() after status update instead of loadRequests()?

If a staff member has filtered to show only "open" requests and updates one to "in_progress", calling `loadRequests()` would reset the filters. Calling `applyFilters()` reloads with the same filters still active — so the updated record disappears from the filtered view, which is the correct behavior.

### How does the WHERE clause filtering work in SQLModel?

```python
query = select(ServiceRequest)
# query currently selects ALL rows

query = query.where(ServiceRequest.category == "maintenance")
# query now has: WHERE category = 'maintenance'

query = query.where(ServiceRequest.status == "open")
# query now has: WHERE category = 'maintenance' AND status = 'open'

results = session.exec(query).all()
# executes the SQL and returns matching rows as Python objects
```

Each `.where()` call adds an `AND` condition. Filters are only applied if the parameter was actually provided — `Optional[str] = Query(default=None)` means if the user doesn't pick a filter, that parameter is `None` and the WHERE clause is skipped.

### What is the business value of the recommended action field?

Without it, a staff member receives a classified request and still has to decide what to do next — adding cognitive load and inconsistency. The recommended action removes that decision for common cases, standardizes the response, and reduces the time between request receipt and action. For a city department handling hundreds of requests per day, that is measurable operational efficiency.

---

## Folder Structure After Week 2 Complete

```
city-service-triage-agent/
├── backend/
│   ├── venv/
│   ├── database.db
│   ├── database.py        ← unchanged
│   ├── models.py          ← added recommended_action field
│   ├── schemas.py         ← added recommended_action to output
│   ├── triage.py          ← NEW: classifier + action generator
│   └── main.py            ← updated: filters + PATCH status endpoint
├── frontend/
│   └── index.html         ← updated: filter bar + badges + status dropdown
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   ├── 03_day3_api_endpoints.md
│   ├── 04_day4_frontend.md
│   ├── 05_day5_logical_structure.md
│   ├── 06_week2_triage_classifier.md
│   └── 07_week2_day3_5_dashboard.md    ← this file
├── mcp/
└── .gitignore
```

---

## Git Commit — End of Week 2

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Week 2 complete: dashboard filters, status updates, recommended actions"
git push
```

---

## Week 2 Completion Checklist

- [ ] triage.py created with classify_request() function
- [ ] POST /requests auto-classifies every new request
- [ ] category and priority no longer null in database
- [ ] recommended_action stored and displayed
- [ ] PATCH /requests/{id}/status updates status correctly
- [ ] GET /requests supports category, priority, status filters
- [ ] Dashboard shows color-coded category and priority badges
- [ ] Status dropdown in table updates live
- [ ] Filter bar works individually and combined
- [ ] Clear filters resets all dropdowns and reloads
- [ ] Record count shows number of matching results
- [ ] All changes pushed to GitHub

---

## Next Step

→ **Week 3 Day 1-2:** Build the MCP server — expose your app's
functions as tools that an AI agent can call via the
Model Context Protocol.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Week 2 Day 3-5 — Dashboard Filters and Status Updates*
