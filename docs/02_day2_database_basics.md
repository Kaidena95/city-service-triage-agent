# Day 2 — Database Basics
## City Service Triage Agent

> **Purpose:** Documents everything learned and built on Day 2 — relational databases, SQLite, SQLModel, ORM concepts, and connecting the database to FastAPI.

---

## What Was Learned

### What is a Relational Database?

A relational database is like a permanent spreadsheet that lives on your computer. It has:

| Term | What it means |
|------|--------------|
| **Table** | Like one sheet in a spreadsheet — holds one type of data |
| **Row** | One record — one service request submitted by a citizen |
| **Column** | One field — id, description, location, category, etc. |
| **Relationship** | How tables link to each other (one table for now, more later) |

Every time a citizen submits a request, a new **row** is added to the `ServiceRequest` **table**.

---

### What is SQLite?

SQLite is a database that lives in a single file on your computer — `database.db` in your project folder.

| Feature | Detail |
|---------|--------|
| No installation needed | Comes built into Python |
| No server needed | Just a file on disk |
| No password needed | Perfect for development |
| Production swap | In a real city system, swap for PostgreSQL — same SQL language |

---

### What is SQLModel?

A Python library that lets you define your database table as a Python class instead of writing raw SQL.

**Without SQLModel (raw SQL):**
```sql
CREATE TABLE servicerequest (
  id INTEGER PRIMARY KEY,
  description TEXT NOT NULL,
  location TEXT NOT NULL
);
```

**With SQLModel (Python class):**
```python
class ServiceRequest(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    description: str
    location: str
```

Same result — but the Python version also gives you:
- Type checking and auto-validation
- Direct integration with FastAPI
- One definition that serves as database table + API schema

---

### What is an ORM?

ORM = Object Relational Mapper. It translates between Python and the database.

| Python world | Database world |
|-------------|---------------|
| A class | A table |
| An instance of that class | A row in the table |
| An attribute (`request.status`) | A column value |
| `session.get(ServiceRequest, 5)` | `SELECT * FROM servicerequest WHERE id = 5` |

You write Python — the ORM writes SQL for you behind the scenes.

---

## Environment Setup

### Mac — Activate Virtual Environment

Always activate before running any commands:

```bash
# WHERE: city-service-triage-agent/backend/
source venv/bin/activate
```

Confirm `(venv)` appears in your terminal prompt:
```
(venv) yourname@computer backend %
```

### Install SQLModel

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
pip install sqlmodel
```

Verify installation:
```bash
pip show sqlmodel
```

Expected output:
```
Name: sqlmodel
Version: 0.0.x
Location: /Users/yourname/.../backend/venv/...
```

Update to latest version if needed:
```bash
pip install --upgrade sqlmodel
```

---

## Files Created

### File 1 — `backend/models.py`

Defines the `ServiceRequest` database table as a Python class.

```python
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ServiceRequest(SQLModel, table=True):
    """
    Represents one citizen service request in the database.
    Each instance of this class = one row in the servicerequest table.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    # Optional means it can be None before saving
    # SQLite assigns the actual number automatically (1, 2, 3...)

    description: str
    # The text the citizen typed — what is the problem?

    location: str
    # Where is the problem? Street address, intersection, or landmark

    category: Optional[str] = Field(default=None)
    # Assigned by the triage classifier — NOT filled in by the user
    # Options: maintenance, safety, sanitation, facility, IT

    priority: Optional[str] = Field(default=None)
    # Assigned by the triage classifier — NOT filled in by the user
    # Options: low, medium, high, critical

    status: str = Field(default="open")
    # Lifecycle state of the request
    # Starts as "open" — can become "in_progress" or "resolved"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Timestamp set automatically when the row is created
    # utcnow() = current time in UTC — standard for server timestamps
```

---

### The ServiceRequest Table — Field by Field

| Field | Type | Default | Who sets it | Purpose |
|-------|------|---------|-------------|---------|
| `id` | Integer | Auto (SQLite) | Database | Unique identifier for each request |
| `description` | String | Required | Citizen | What problem was reported |
| `location` | String | Required | Citizen | Where the problem is located |
| `category` | String | None | Triage classifier | Type of issue |
| `priority` | String | None | Triage classifier | How urgent the issue is |
| `status` | String | "open" | System | Current lifecycle state |
| `created_at` | DateTime | Now (UTC) | System | When the request was submitted |

---

### File 2 — `backend/database.py`

Handles the database connection and session management.

```python
from sqlmodel import SQLModel, create_engine, Session

# Connection string — tells SQLModel where the database file lives
# sqlite:///./database.db means:
#   sqlite     = use SQLite
#   ///        = relative path
#   ./         = current folder (backend/)
#   database.db = the file it creates or opens
DATABASE_URL = "sqlite:///./database.db"

# The engine is the connection between Python and the database file
# connect_args is required for SQLite to work safely with FastAPI
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False}
)


def create_db_and_tables():
    """
    Creates the database file and all tables if they do not exist yet.
    Called once when the app starts up.
    """
    SQLModel.metadata.create_all(engine)


def get_session():
    """
    Creates a database session for each request.
    A session is a temporary connection to the database.
    You use it to read and write data, then it closes automatically.
    FastAPI calls this function automatically via dependency injection.
    """
    with Session(engine) as session:
        yield session
```

---

### File 3 — `backend/main.py` (updated)

Updated to connect the database on startup.

```python
from contextlib import asynccontextmanager
from fastapi import FastAPI
from database import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Runs once when the app starts up.
    Creates the database file and tables if they do not exist.
    """
    create_db_and_tables()
    yield


# Pass the lifespan function to FastAPI so it runs on startup
app = FastAPI(lifespan=lifespan)


@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}
```

---

## How to Run

### Step 1 — Start the server

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
uvicorn main:app --reload --reload-exclude 'venv/**'
```

### Step 2 — Confirm database was created

Open a second terminal on Mac:

```
Command + Shift + `
```

Or go to Terminal → New Terminal in VS Code menu.

Then run:

```bash
cd backend
source venv/bin/activate
ls
```

Expected output — you should now see `database.db`:
```
__pycache__    database.db    database.py    main.py    models.py    venv
```

### Step 3 — Inspect the database visually

Install the SQLite Viewer extension in VS Code:
1. Press `Ctrl + Shift + X`
2. Search `SQLite Viewer`
3. Install the one by Florian Klampfer
4. Click `database.db` in the sidebar — you will see the `servicerequest` table with all columns but no rows yet

---

## Terminal Behavior — What is Normal on Mac

| What you see | Normal? | What it means |
|-------------|---------|--------------|
| `Application startup complete` | Yes ✅ | Server running correctly |
| `WatchFiles detected changes. Reloading...` then `startup complete` | Yes ✅ | You saved a file, server restarted |
| `WatchFiles` reloading over and over with no `startup complete` | No ❌ | Loop problem — stop with Ctrl+C |
| `ERROR: Could not import module` | No ❌ | Wrong directory or missing file |

### Stop the server
```bash
Ctrl + C
```

---

## Two Terminal Workflow (Mac)

Running two terminals at once is standard practice:

| Terminal | Purpose |
|----------|---------|
| Terminal 1 | Running the uvicorn server — leave this alone |
| Terminal 2 | Running other commands — git, pip, ls, etc. |

Open second terminal: **Command + Shift + `** or **Terminal → New Terminal**

Always activate venv in each terminal separately:
```bash
source venv/bin/activate
```

---

## Key Concepts — Interview Prep

### Why is `id` Optional with default=None?
Before a row is saved to the database, the id does not exist yet — SQLite assigns it automatically. Making it `Optional[int] = Field(default=None)` tells Python "this can be empty until the database fills it in."

### Why do `category` and `priority` default to None but `status` defaults to "open"?
Category and priority are assigned later by the triage classifier — we do not know them at submission time. Status always starts as "open" because every new request begins in an open state by definition.

### What is the difference between engine and session?
- **Engine** = the permanent connection to the database file. Created once when the app starts. Think of it as the road between your app and the database.
- **Session** = a temporary transaction on that road. Created per request, used to read or write data, then closed. Think of it as one trip on that road.

### Why use `default_factory=datetime.utcnow` instead of `default=datetime.utcnow()`?
- `default=datetime.utcnow()` — the parentheses mean "call this function RIGHT NOW when the class is defined." Every row would get the same timestamp — the time the app started.
- `default_factory=datetime.utcnow` — no parentheses means "call this function each time a new row is created." Every row gets its own correct timestamp.

---

## Folder Structure After Day 2

```
city-service-triage-agent/
├── backend/
│   ├── __pycache__/        ← auto-generated by Python, ignore
│   ├── venv/               ← virtual environment, never touch
│   ├── database.db         ← SQLite database file (auto-created on startup)
│   ├── database.py         ← engine, session, create tables
│   ├── models.py           ← ServiceRequest table definition
│   └── main.py             ← FastAPI app with DB startup
├── docs/
│   ├── 00_dev_environment_setup.md
│   ├── 01_project_roadmap.md
│   └── 02_day2_database_basics.md   ← this file
├── frontend/
├── mcp/
└── .gitignore
```

---

## Git Commit — End of Day 2

```bash
git add .
```

```bash
git commit -m "Day 2: SQLModel database, ServiceRequest table, DB connection"
```

```bash
git push
```

---

## Next Step

→ **Day 3:** Build the actual API endpoints — POST /requests, GET /requests, GET /requests/{id}

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Day 2 — Database Basics*
