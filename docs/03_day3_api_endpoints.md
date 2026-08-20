# Day 3 — API Endpoints
## City Service Triage Agent

> **Purpose:** Documents everything learned and built on Day 3 — creating POST and GET endpoints, request schemas, dependency injection, and testing with Swagger UI.

---

## What Was Built

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `GET /` | GET | Health check — confirms API is running |
| `GET /health` | GET | Health check with status field |
| `POST /requests` | POST | Accept and save a new service request |
| `GET /requests` | GET | Return all service requests |
| `GET /requests/{id}` | GET | Return one request by ID, 404 if not found |

---

## Core Concepts

### What is a Request Body?

When a citizen submits a service request, they send data TO your API in the **request body** — a JSON object:

```json
{
  "description": "There is a broken streetlight near 5th and Main",
  "location": "5th Street and Main Street"
}
```

FastAPI reads this automatically, validates it, and passes it to your function as a Python object. If a required field is missing, FastAPI returns a `422` error automatically — no validation logic needed.

---

### What is a Path Parameter?

In `GET /requests/{id}` the `{id}` is a **path parameter** — the ID is part of the URL:

```
GET /requests/1    → return request with id 1
GET /requests/5    → return request with id 5
GET /requests/99   → return request with id 99
```

FastAPI extracts the number from the URL and passes it to your function automatically.

---

### What is Dependency Injection?
In FastAPI, dependency injection is how the database session gets passed into your endpoint functions. Instead of creating a session manually inside every function, you declare it as a parameter and FastAPI handles it:

So, Instead of creating a database session manually inside every function, you declare it as a parameter and FastAPI handles it:

```python
def get_all_requests(session: Session = Depends(get_session)):
```

`Depends(get_session)` tells FastAPI: "before calling this function, run `get_session()` and pass the result in as `session`." The session opens and closes correctly every time automatically.

---

### What is a Schema vs a Model?

| Type | Purpose | Example |
|------|---------|---------|
| **Model** (`table=True`) | Defines the database table | `ServiceRequest` in `models.py` |
| **Schema** | Defines what the API accepts or returns | `ServiceRequestCreate`, `ServiceRequestRead` |

Why separate? What the user sends in (description + location only) is different from what the database stores (all fields). Keeping them separate gives control over what data is exposed through the API.

---

## Environment Setup

```bash
# Step 1 — go to backend
cd backend

# Step 2 — activate venv (Mac)
source venv/bin/activate

# Step 3 — verify Day 2 files exist
ls
```

Expected output:
```
__pycache__    database.db    database.py    main.py    models.py    venv
```

All five must be present before continuing.

---

## Files Created / Updated

### New File — `backend/schemas.py`

Defines what data the API accepts and returns — separate from the database model.

```python
from typing import Optional
from sqlmodel import SQLModel


class ServiceRequestCreate(SQLModel):
    """
    Defines what data the API accepts when creating a new request.
    Only description and location — the citizen fills these in.
    Everything else is assigned automatically by the system.
    """
    description: str
    location: str


class ServiceRequestRead(SQLModel):
    """
    Defines what data the API returns when reading a request.
    Includes all fields including the ones the system assigned.
    """
    id: int
    description: str
    location: str
    category: Optional[str]
    priority: Optional[str]
    status: str
    created_at: str

    class Config:
        from_attributes = True
```

---

### Updated — `backend/models.py`

```python
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ServiceRequest(SQLModel, table=True):
    """
    The actual database table definition.
    Each instance = one row in the servicerequest table.
    """
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    location: str
    category: Optional[str] = Field(default=None)
    priority: Optional[str] = Field(default=None)
    status: str = Field(default="open")
    created_at: str = Field(
        default_factory=lambda: datetime.utcnow().isoformat()
    )
```

---

### Updated — `backend/main.py`

```python
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import ServiceRequest
from schemas import ServiceRequestCreate, ServiceRequestRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup — creates DB tables if they don't exist."""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)


# ENDPOINT 1 — Health check
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ENDPOINT 2 — Create a new service request
# Method: POST
# URL: /requests
# Body: { "description": "...", "location": "..." }
# Returns: the full saved request including id and timestamps
@app.post("/requests", response_model=ServiceRequestRead)
def create_request(
    request_data: ServiceRequestCreate,
    session: Session = Depends(get_session)
):
    db_request = ServiceRequest(
        description=request_data.description,
        location=request_data.location
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


# ENDPOINT 3 — Get all service requests
# Method: GET
# URL: /requests
# Returns: list of all requests in the database
@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(session: Session = Depends(get_session)):
    requests = session.exec(select(ServiceRequest)).all()
    return requests


# ENDPOINT 4 — Get one service request by ID
# Method: GET
# URL: /requests/{id}
# Returns: one request, or 404 if not found
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
```

---

## How to Run

### Step 1 — Delete old database (model changed)

```bash
# WHERE: city-service-triage-agent/backend/
rm database.db
```

### Step 2 — Start the server

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
uvicorn main:app --reload --reload-exclude 'venv/**'
```

Wait for:
```
INFO:     Application startup complete.
```

---

## Testing in Swagger UI

Open browser: `http://127.0.0.1:8000/docs`

### Test 1 — Create first request (POST /requests)

Click `POST /requests` → Try it out → paste this body → Execute:

```json
{
  "description": "There is a broken streetlight near 5th and Main",
  "location": "5th Street and Main Street, Los Angeles"
}
```

Expected response (200):
```json
{
  "id": 1,
  "description": "There is a broken streetlight near 5th and Main",
  "location": "5th Street and Main Street, Los Angeles",
  "category": null,
  "priority": null,
  "status": "open",
  "created_at": "2025-01-01T12:00:00"
}
```

### Test 2 — Create second request

```json
{
  "description": "Large pothole damaging vehicles on Wilshire Blvd",
  "location": "Wilshire Boulevard near Vermont Ave"
}
```

### Test 3 — Get all requests (GET /requests)

Click `GET /requests` → Try it out → Execute

Expected: list containing both requests you created.

### Test 4 — Get one request (GET /requests/{id})

Click `GET /requests/{request_id}` → Try it out → enter `1` → Execute

Expected: just the first request.

### Test 5 — Test 404 behavior

Same endpoint, enter `999` as the id.

Expected response (404):
```json
{
  "detail": "Request with id 999 not found"
}
```

---

## What Happens Step by Step — POST /requests

When you click Execute in /docs, here is exactly what happens:

```
1. Browser sends HTTP POST to http://127.0.0.1:8000/requests
   with JSON body { "description": "...", "location": "..." }

2. Uvicorn receives the request and passes it to FastAPI

3. FastAPI matches the URL and method to the create_request() function

4. FastAPI validates the body against ServiceRequestCreate schema
   → if description or location is missing, returns 422 automatically

5. FastAPI calls get_session() via Depends and opens a DB session

6. create_request() runs:
   → creates a ServiceRequest object with description and location
   → category, priority = None (triage classifier not wired yet)
   → status = "open" (default)
   → created_at = current UTC timestamp (auto)

7. session.add(db_request) — stages the object for saving

8. session.commit() — writes the row to database.db

9. session.refresh(db_request) — reloads from DB to get auto-assigned id

10. FastAPI serializes the object using ServiceRequestRead schema

11. Returns JSON response with status code 200
```

---

## HTTP Status Codes Used

| Code | Meaning | When it happens |
|------|---------|----------------|
| `200` | OK | Successful GET or POST |
| `404` | Not Found | Request ID does not exist in database |
| `422` | Unprocessable Entity | Required field missing in request body |

---

## Folder Structure After Day 3

```
city-service-triage-agent/
├── backend/
│   ├── __pycache__/
│   ├── venv/
│   ├── database.db        ← recreated fresh with new schema
│   ├── database.py        ← unchanged from Day 2
│   ├── models.py          ← updated: created_at now stores as string
│   ├── main.py            ← updated: three new endpoints added
│   └── schemas.py         ← NEW: ServiceRequestCreate, ServiceRequestRead
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   └── 03_day3_api_endpoints.md    ← this file
├── frontend/
├── mcp/
└── .gitignore
```

---

## Interview Prep — Key Questions

### Why two schema classes instead of using ServiceRequest for everything?
`ServiceRequest` has fields the user should never set directly — like `id` (assigned by DB), `category` and `priority` (assigned by classifier), `created_at` (assigned by system). If you used `ServiceRequest` as the input schema, a user could send `{"id": 999, "status": "resolved"}` and bypass your business logic. Separate schemas give you control over what comes in vs what goes out.

### What does Depends(get_session) actually do?
It tells FastAPI to run `get_session()` before calling your endpoint function, and pass the result in as the `session` parameter. This is dependency injection — it keeps session management out of your business logic and ensures the session is always properly opened and closed.

### Why call session.refresh() after session.commit()?
After `commit()`, the database assigns the `id` — but your Python object doesn't know that yet. `refresh()` reloads the object from the database so the `id` field is populated before you return it in the response.

### Why return a 404 instead of just returning None?
HTTP status codes are a contract with whoever is calling your API — frontend, mobile app, another service. Returning `None` with a `200` status says "success, here's nothing" which is confusing. A `404` clearly communicates "this resource does not exist" so the caller knows exactly what happened.

---

## Git Commit — End of Day 3

```bash
cd ~/Desktop/city-service-triage-agent
```

```bash
git add .
```

```bash
git commit -m "Day 3: POST and GET endpoints for service requests"
```

```bash
git push
```

---

## Next Step

→ **Day 4:** Build the HTML frontend form that calls your API

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Day 3 — API Endpoints*
