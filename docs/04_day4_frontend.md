# Day 4 — Simple Frontend
## City Service Triage Agent

> **Purpose:** Documents everything learned and built on Day 4 — building a plain HTML frontend form and dashboard that communicates with the FastAPI backend.

---

## What Was Built

A single `frontend/index.html` file containing:
- A service request submission form (description + location fields)
- A dashboard table showing all submitted requests pulled from the API
- JavaScript `fetch()` calls connecting the frontend to the backend

---

## Data Flow

```
Citizen fills form
      ↓
JavaScript fetch() sends POST /requests with JSON body
      ↓
FastAPI saves to database.db
      ↓
JavaScript fetch() sends GET /requests
      ↓
Dashboard table renders the results
```

---

## Core Concepts

### What is fetch()?

`fetch()` is a built-in JavaScript function that sends HTTP requests from the browser to an API — exactly what you were doing manually in Swagger UI, but automated.

```javascript
// POST — submit a new request
fetch("http://127.0.0.1:8000/requests", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
        description: "Broken streetlight",
        location: "5th and Main"
    })
})

// GET — load all requests
fetch("http://127.0.0.1:8000/requests")
```

---

### What is CORS?

CORS (Cross-Origin Resource Sharing) is a browser security rule. When your HTML file tries to call your API running on port 8000, the browser blocks it by default — they are considered different "origins."

Fix: add CORS middleware to FastAPI that says "allow requests from any origin."

Without CORS in main.py:
```
Browser blocks the fetch() call
Console shows: "Access-Control-Allow-Origin" error
Dashboard shows: "Cannot connect to API"
```

With CORS added:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # allow all origins
    allow_methods=["*"],    # allow GET, POST, etc.
    allow_headers=["*"],    # allow all headers
)
```

---

### What is async/await?

Network requests (like `fetch()`) take time — you don't know when the API will respond. `async/await` lets JavaScript wait for the response without freezing the entire page.

```javascript
// Without async/await — broken, response not ready yet
const response = fetch(url);       // response is a Promise, not data
const data = response.json();      // error — .json() doesn't exist on a Promise

// With async/await — correct
async function loadRequests() {
    const response = await fetch(url);   // wait for response
    const data = await response.json();  // wait for JSON parsing
    // now data is the actual array of requests
}
```

---

## Environment Setup

### Verify before starting

```bash
# Terminal 1 — run the server
cd ~/Desktop/city-service-triage-agent/backend
source venv/bin/activate
uvicorn main:app --reload --reload-exclude 'venv/**'
```

Wait for `Application startup complete.`

```bash
# Terminal 2 — for other commands
# Command + Shift + ` to open second terminal
cd ~/Desktop/city-service-triage-agent
```

---

## Files Updated / Created

### Updated — `backend/main.py`

Added CORS middleware so the browser allows frontend-to-API communication.

```python
from contextlib import asynccontextmanager
from typing import List
from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import ServiceRequest
from schemas import ServiceRequestCreate, ServiceRequestRead


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# CORS middleware — allows browser requests from any origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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
    db_request = ServiceRequest(
        description=request_data.description,
        location=request_data.location
    )
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request


@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(session: Session = Depends(get_session)):
    requests = session.exec(select(ServiceRequest)).all()
    return requests


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

### New File — `frontend/index.html`

Single HTML file containing the form, dashboard, styles, and JavaScript.

Key sections:

**Form section** — citizen input:
```html
<textarea id="description" placeholder="Describe the issue..."></textarea>
<input type="text" id="location" placeholder="Street address or intersection"/>
<button onclick="submitRequest()">Submit Request</button>
```

**Dashboard section** — displays all requests:
```html
<table>
  <thead>
    <tr>
      <th>#</th><th>Description</th><th>Location</th>
      <th>Category</th><th>Priority</th><th>Status</th><th>Submitted</th>
    </tr>
  </thead>
  <tbody id="requests-table"></tbody>
</table>
```

**JavaScript — submit function:**
```javascript
async function submitRequest() {
    const description = document.getElementById("description").value.trim();
    const location    = document.getElementById("location").value.trim();

    if (!description || !location) {
        // show validation error
        return;
    }

    const response = await fetch("http://127.0.0.1:8000/requests", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description, location })
    });

    const saved = await response.json();
    // clear form, show success, reload dashboard
    loadRequests();
}
```

**JavaScript — load dashboard:**
```javascript
async function loadRequests() {
    const response = await fetch("http://127.0.0.1:8000/requests");
    const requests = await response.json();
    // build table rows from requests array
}
```

---

## How to Open the Frontend

```bash
# Mac — open in default browser
open ~/Desktop/city-service-triage-agent/frontend/index.html
```

Or in VS Code sidebar: right-click `index.html` → Reveal in Finder → double-click

---

## Testing Checklist

| Test | What to do | Expected result |
|------|-----------|----------------|
| Dashboard loads | Open the page | Existing requests appear in table |
| Submit new request | Fill form, click Submit | Success message + new row in table |
| Empty field validation | Click Submit with empty fields | "Please fill in both fields" error |
| API down | Stop uvicorn, reload page | "Cannot connect to API" message in table |
| Priority badges | Check existing rows | Shows "pending" badge (triage not wired yet) |

---

## What Happens Step by Step — Form Submission

```
1. Citizen types description and location into the form

2. Citizen clicks "Submit Request" button

3. JavaScript onclick calls submitRequest()

4. submitRequest() reads both field values
   → if either is empty: shows error, stops here

5. fetch() sends HTTP POST to http://127.0.0.1:8000/requests
   with Content-Type: application/json
   and body: { "description": "...", "location": "..." }

6. FastAPI receives the request
   → CORS middleware checks the origin — allows it
   → Routes to create_request() function
   → Validates body against ServiceRequestCreate schema
   → Opens a database session via Depends(get_session)

7. create_request() creates ServiceRequest object
   → category = None (triage not wired yet)
   → priority = None (triage not wired yet)
   → status = "open"
   → created_at = current UTC timestamp

8. session.commit() writes row to database.db

9. FastAPI returns JSON response with full saved record

10. JavaScript receives the response
    → Shows "Request #X submitted successfully"
    → Clears the form fields
    → Calls loadRequests() to refresh the dashboard

11. loadRequests() sends GET /requests to the API
    → API returns all rows from database
    → JavaScript builds HTML table rows
    → Dashboard updates with the new request visible
```

---

## Key Differences — What Form Sends vs What API Returns

| Direction | Data |
|-----------|------|
| Form → API (POST body) | `description`, `location` only |
| API → Form (response) | `id`, `description`, `location`, `category`, `priority`, `status`, `created_at` |

The user provides 2 fields. The system fills in the rest automatically.

---

## Interview Prep

### Why plain HTML instead of React?
The internship evaluates backend and agentic logic, not UI frameworks. Plain HTML + JavaScript is faster to write, easier to explain, and demonstrates you understand the fundamentals — fetch, async/await, DOM manipulation — without framework magic hiding what's happening.

### What is CORS and why is it needed?
Browsers enforce a security rule that prevents a page on one "origin" from calling an API on a different origin. Since the HTML file and the API run on different ports (or one is a file), the browser blocks the request. Adding CORS middleware to FastAPI tells the browser explicitly that cross-origin requests are permitted.

### Why does loadRequests() run on page load?
Without it, the dashboard would be empty until the user submits something. Calling it immediately on page open (`loadRequests()` at the bottom of the script) pre-fills the dashboard with all existing data from the database — giving the user immediate context.

### What does async/await do?
Network requests are asynchronous — they take unknown amounts of time. `async/await` tells JavaScript to pause that specific function and wait for the response before continuing, without freezing the rest of the page. Without it, you'd try to use the response data before it arrived.

---

## Folder Structure After Day 4

```
city-service-triage-agent/
├── backend/
│   ├── __pycache__/
│   ├── venv/
│   ├── database.db
│   ├── database.py
│   ├── models.py
│   ├── main.py          ← updated: CORS middleware added
│   └── schemas.py
├── frontend/
│   └── index.html       ← NEW: form + dashboard
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   ├── 02_day2_database_basics.md
│   ├── 03_day3_api_endpoints.md
│   └── 04_day4_frontend.md    ← this file
├── mcp/
└── .gitignore
```

---

## Git Commit — End of Day 4

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Day 4: HTML frontend form and dashboard connected to API"
git push
```

---

## Next Step

→ **Day 5:** Write the logical structure document while everything is fresh, then begin Week 2 — triage classifier.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Day 4 — Frontend*
