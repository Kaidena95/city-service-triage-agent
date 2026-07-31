# Week 2 Day 1-2 — Rules-Based Triage Classifier
## City Service Triage Agent

> **Purpose:** Documents the triage classifier — the AI agent layer that automatically assigns category, priority, and recommended action to every service request.

---

## What Changed This Week

Before Week 2 every request stored `category=null` and `priority=null`.
After Week 2 every request is automatically classified on submission.

```
BEFORE:
POST /requests → stored with category=null, priority=null

AFTER:
POST /requests
  → triage.py classify_request(description)
  → category="maintenance", priority="high"
  → recommended_action="Schedule repair crew within 24 hours"
  → stored with all fields populated
```

---

## Why Rules-Based Over Machine Learning

| Factor | Rules-Based | ML Model |
|--------|-------------|----------|
| Explainability | Every decision fully traceable | Black box |
| Documentation | Written in plain markdown | Requires model weights |
| Gemini test | Fully reproducible from docs | Cannot regenerate weights |
| Testability | 100% predictable with pytest | Probabilistic |
| Interview defense | Explain every single line | Hard to justify decisions |

Design note: The classifier uses deterministic keyword matching and
can be replaced with an LLM-based classifier in production without
changing the interface — same inputs, same outputs.

---

## How the Classifier Works

```
Input: "There is a broken streetlight near 5th and Main"

Step 1 — normalize text to lowercase

Step 2 — score each category by keyword matches:
  safety:      0 matches
  maintenance: 2 matches ("broken", "streetlight")
  sanitation:  0 matches
  facility:    0 matches
  IT:          0 matches
  → best_category = "maintenance"

Step 3 — score each priority level:
  critical: 0 matches
  high:     1 match ("broken")
  medium:   1 match ("pothole" — not found)
  low:      0 matches
  → scan in order critical→high→medium→low
  → first match found: best_priority = "high"

Step 4 — look up ACTION_MAP["maintenance"]["high"]
  → "Schedule repair crew within 24 hours. Flag as priority work order."

Output:
  category = "maintenance"
  priority = "high"
  recommended_action = "Schedule repair crew within 24 hours..."
```

---

## Environment Setup

```bash
# Step 1 — go to project root
cd ~/Desktop/city-service-triage-agent

# Step 2 — go into backend
cd backend

# Step 3 — activate venv (Mac)
source venv/bin/activate

# Step 4 — verify files
ls
```

Expected:
```
__pycache__  database.db  database.py  main.py  models.py  schemas.py  triage.py  venv
```

```bash
# Step 5 — start the server in Terminal 1
uvicorn main:app --reload --reload-exclude 'venv/**'
```

---

## Files Created / Updated

### New File — `backend/triage.py`

```python
CATEGORY_KEYWORDS = {
    "safety": ["danger", "emergency", "fire", "injury", "hazard", ...],
    "maintenance": ["streetlight", "pothole", "broken", "repair", ...],
    "sanitation": ["trash", "garbage", "waste", "dumping", "rodent", ...],
    "facility": ["park", "building", "restroom", "playground", ...],
    "IT": ["website", "portal", "login", "password", "system", ...]
}

PRIORITY_KEYWORDS = {
    "critical": ["emergency", "fire", "injury", "gas leak", ...],
    "high": ["broken", "damaged", "unsafe", "blocking", ...],
    "medium": ["pothole", "crack", "graffiti", "trash", ...],
    "low": ["park", "bench", "website", "inquiry", ...]
}

ACTION_MAP = {
    "safety": {
        "critical": "Dispatch emergency response team immediately.",
        "high": "Alert safety department within 4 hours.",
        ...
    },
    "maintenance": {
        "critical": "Dispatch repair crew immediately.",
        "high": "Schedule repair crew within 24 hours.",
        ...
    },
    ...
}

def classify_request(description: str) -> dict:
    text = description.lower()

    # Score categories
    category_scores = {
        cat: sum(1 for kw in kws if kw in text)
        for cat, kws in CATEGORY_KEYWORDS.items()
    }
    best_category = max(category_scores, key=category_scores.get)
    if category_scores[best_category] == 0:
        best_category = "general"

    # Score priorities — scan in order, take first match
    priority_order = ["critical", "high", "medium", "low"]
    best_priority = "low"
    for p in priority_order:
        if sum(1 for kw in PRIORITY_KEYWORDS[p] if kw in text) > 0:
            best_priority = p
            break

    recommended_action = ACTION_MAP
        .get(best_category, ACTION_MAP["general"])[best_priority]

    return {
        "category": best_category,
        "priority": best_priority,
        "recommended_action": recommended_action
    }
```

---

### Updated — `backend/models.py`

Added `recommended_action` field:

```python
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

---

### Updated — `backend/schemas.py`

Added `recommended_action` to output schema:

```python
class ServiceRequestRead(SQLModel):
    id: int
    description: str
    location: str
    category: Optional[str]
    priority: Optional[str]
    status: str
    recommended_action: Optional[str]
    created_at: str

    class Config:
        from_attributes = True
```

---

### Updated — `backend/main.py`

Two key changes:

**1 — POST /requests now calls classifier:**
```python
from triage import classify_request

@app.post("/requests", response_model=ServiceRequestRead)
def create_request(request_data, session):
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
```

**2 — New PATCH endpoint for status updates:**
```python
@app.patch("/requests/{request_id}/status")
def update_status(request_id: int, status: str, session):
    valid_statuses = ["open", "in_progress", "resolved"]
    if status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")
    db_request = session.get(ServiceRequest, request_id)
    if not db_request:
        raise HTTPException(status_code=404, detail="Not found")
    db_request.status = status
    session.commit()
    session.refresh(db_request)
    return db_request
```

---

## Test Cases — Manual Verification

Run these in a Python shell to verify the classifier:

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
python3
```

```python
from triage import classify_request

# Test 1 — maintenance request
print(classify_request("broken streetlight near 5th and Main"))
# Expected: category=maintenance, priority=high

# Test 2 — safety emergency
print(classify_request("gas leak near the park, dangerous emergency"))
# Expected: category=safety, priority=critical

# Test 3 — sanitation complaint
print(classify_request("illegal garbage dumping with rats everywhere"))
# Expected: category=sanitation, priority=high

# Test 4 — IT request
print(classify_request("cannot login to the city portal password not working"))
# Expected: category=IT, priority=low

# Test 5 — vague description
print(classify_request("something needs to be fixed"))
# Expected: category=general, priority=low
```

Exit Python shell:
```python
exit()
```

---

## API Endpoints After Week 2

| Method | Path | What it does |
|--------|------|-------------|
| GET | `/` | Health check |
| GET | `/health` | Health check with status |
| POST | `/requests` | Create request + auto-classify |
| GET | `/requests` | List all requests |
| GET | `/requests/{id}` | Get one request |
| PATCH | `/requests/{id}/status` | Update status only |

---

## Important — Delete Database When Schema Changes

Any time you add a field to `models.py`, the old `database.db`
file has the wrong schema and must be deleted:

```bash
# WHERE: city-service-triage-agent/backend/
rm database.db
```

The server auto-creates a fresh database with the correct schema
on next startup. All old test data is lost — that is fine in
development. In production you would write a migration script
instead of deleting the database.

---

## HTTP Status Codes Added This Week

| Code | Meaning | When it occurs |
|------|---------|---------------|
| 400 | Bad Request | Invalid status value in PATCH |
| 404 | Not Found | Request ID does not exist |

---

## Data Flow — Full Classified Request

```
Citizen submits: description + location
        ↓
FastAPI create_request() runs
        ↓
classify_request(description) called
  → text lowercased
  → category keywords scanned → best_category found
  → priority keywords scanned → best_priority found
  → ACTION_MAP lookup → recommended_action returned
        ↓
ServiceRequest built:
  description     = citizen input
  location        = citizen input
  category        = from classifier
  priority        = from classifier
  recommended_action = from classifier
  status          = "open" (default)
  created_at      = UTC now (auto)
        ↓
Written to database.db
        ↓
Full record returned to frontend
        ↓
Dashboard shows category + priority + recommended action
```

---

## Folder Structure After Week 2 Day 1-2

```
city-service-triage-agent/
├── backend/
│   ├── venv/
│   ├── database.db          ← recreated with new schema
│   ├── database.py          ← unchanged
│   ├── models.py            ← updated: added recommended_action
│   ├── schemas.py           ← updated: added recommended_action
│   ├── main.py              ← updated: classifier wired in + PATCH endpoint
│   └── triage.py            ← NEW: classifier + action generator
├── frontend/
│   └── index.html
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   ├── 03_day3_api_endpoints.md
│   ├── 04_day4_frontend.md
│   ├── 05_day5_logical_structure.md
│   └── 06_week2_triage_classifier.md    ← this file
├── mcp/
└── .gitignore
```

---

## Interview Prep

### Why rules-based over ML?
Deterministic classifiers are fully explainable — every decision can be traced to a specific keyword match. For this submission, the Gemini regeneration test requires logic that can be expressed in plain markdown. ML model weights cannot be documented that way. In production, the interface stays the same — just swap the `classify_request()` function body.

### What does `sum(1 for keyword in keywords if keyword in text)` do?
It is a generator expression inside `sum()`. For each keyword in the list, it yields `1` if that keyword appears in the text, `0` if not. `sum()` adds them all up giving a count of how many keywords matched. It is a concise Python one-liner equivalent to a for loop with a counter.

### Why PATCH instead of PUT for status update?
`PUT` replaces an entire resource — you would send all fields. `PATCH` updates only specific fields — you send just what changed. Since we only want to change `status` without affecting description, location, category or any other field, `PATCH` is semantically correct.

### Why delete the database when adding a column?
SQLite does not automatically add new columns to existing tables. The old `database.db` was created with the old schema — it has no `recommended_action` column. Deleting it forces SQLModel to recreate the table with the correct schema on next startup. In production you would write an `ALTER TABLE` migration instead.

---

## Git Commit — End of Week 2 Day 1-2

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Week 2 Day 1-2: rules-based triage classifier wired into API"
git push
```

---

## Next Step

→ **Week 2 Day 3:** Update the frontend dashboard to display category,
priority badges, recommended actions, and status update controls.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Week 2 Day 1-2 — Triage Classifier*
