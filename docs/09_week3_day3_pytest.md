# Week 3 Day 3 — pytest Tests
## City Service Triage Agent

> **Purpose:** Documents the test suite for the triage classifier and API endpoints — verifying correctness, enabling confident refactoring, and demonstrating production-quality code for the submission.

---

## Why Tests Matter for This Submission

Two specific reasons this project needs tests:

**Credibility:** A project with tests signals production-quality engineering. The internship team reviews your GitHub repo — tests show you write code that can be verified, not just code that happens to work.

**Gemini regeneration test:** The submission docs must be precise enough for an AI to regenerate the app. Tests prove the regenerated app actually works correctly — if someone follows your docs and the tests pass, the regeneration succeeded.

---

## Core Concepts

### What is pytest?

Python's standard testing framework. You write functions that assert your code does what you expect — automatically, every time.

```python
def test_classify_maintenance():
    result = classify_request("broken streetlight near 5th")
    assert result["category"] == "maintenance"
    assert result["priority"] == "high"
```

pytest finds functions starting with `test_`, runs them, and reports:
- PASSED ✅ — assertion was true
- FAILED ❌ — assertion was false, shows exactly what went wrong

### What is assert?

`assert expression` means "this must be true, otherwise fail immediately."

```python
assert response.status_code == 200      # must be 200
assert data["category"] == "maintenance" # must be maintenance
assert len(results) == 2                 # must have 2 items
```

If any assert fails, pytest stops that test and reports the failure with the actual vs expected values.

### Unit Test vs Integration Test

| Type | Tests | Example in this project |
|------|-------|------------------------|
| Unit test | One function in isolation | `test_triage.py` — tests `classify_request()` directly |
| Integration test | Multiple components together | `test_api.py` — tests full request → API → database flow |

Both types are needed. Unit tests pinpoint exactly which function broke. Integration tests verify the whole system works end to end.

### What is TestClient?

FastAPI's built-in test utility that lets you send HTTP requests to your app without running uvicorn. Tests run faster and don't depend on a server being up.

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.post("/requests", json={"description": "...", "location": "..."})
assert response.status_code == 200
```

### What is a pytest Fixture?

A function that sets up something needed by your tests and tears it down after. Decorated with `@pytest.fixture`.

```python
@pytest.fixture(name="client")
def client_fixture(session):
    # setup — runs before each test
    app.dependency_overrides[get_session] = lambda: session
    client = TestClient(app)
    yield client           # ← test runs here
    # teardown — runs after each test
    app.dependency_overrides.clear()
```

### Why In-Memory Database for Tests?

```python
engine = create_engine("sqlite://", ...)  # no file path = in-memory
```

- Tests never touch your real `database.db`
- Every test run starts with a clean empty database
- Tests run fast — no file I/O
- Tests are isolated — one test's data doesn't affect another
- Can run tests in any order safely

### What is dependency_overrides?

FastAPI's way of swapping out dependencies for tests. Your endpoints use `get_session` to get a database session. In tests you replace it with a session pointing to the in-memory database instead.

```python
# Normal app — uses real database.db
app.dependency_overrides[get_session] = get_session_override

# Test — uses in-memory database
def get_session_override():
    return session   # the test session

app.dependency_overrides[get_session] = get_session_override
```

---

## Environment Setup

```bash
# Step 1 — go to backend, activate venv
cd ~/Desktop/city-service-triage-agent/backend
source venv/bin/activate

# Step 2 — install pytest
pip install pytest pytest-asyncio httpx

# Step 3 — verify
pip show pytest

# Step 4 — create tests folder
mkdir tests
touch tests/__init__.py

# Step 5 — verify
ls tests/
```

Expected:
```
__init__.py
```

---

## Files Created

### `backend/tests/__init__.py`

Empty file. Tells Python the `tests/` folder is a package so pytest can find the tests.

---

### `backend/tests/test_triage.py`

13 unit tests for the `classify_request()` classifier function.

Tests cover:
- Correct category for each type (maintenance, safety, sanitation, facility, IT)
- Correct priority for each urgency level
- Default to general/low for vague descriptions
- Return structure always contains all three fields
- Priority always one of four valid values
- Category always one of six valid values
- Case insensitive matching works
- Recommended action never empty

---

### `backend/tests/test_api.py`

18 integration tests for the FastAPI endpoints.

Tests cover:

| Endpoint | Tests |
|----------|-------|
| POST /requests | Success, auto-classification, missing fields, default status |
| GET /requests | Empty list, returns all, filter by category, filter by status |
| GET /requests/{id} | Returns correct request, 404 on missing |
| PATCH /requests/{id}/status | Success, to resolved, invalid status, 404 on missing |
| GET / | Returns running message |
| GET /health | Returns ok status |

---

## How to Run Tests

### Run all tests with verbose output

```bash
# WHERE: city-service-triage-agent/backend/  (venv active)
pytest tests/ -v
```

### Run only classifier tests

```bash
pytest tests/test_triage.py -v
```

### Run only API tests

```bash
pytest tests/test_api.py -v
```

### Run one specific test

```bash
pytest tests/test_triage.py::test_classify_safety_emergency -v
```

### Run with summary only (no verbose)

```bash
pytest tests/
```

---

## Expected Output

```
tests/test_triage.py::test_classify_maintenance_streetlight PASSED
tests/test_triage.py::test_classify_maintenance_pothole PASSED
tests/test_triage.py::test_classify_safety_emergency PASSED
tests/test_triage.py::test_classify_safety_fire PASSED
tests/test_triage.py::test_classify_sanitation PASSED
tests/test_triage.py::test_classify_facility PASSED
tests/test_triage.py::test_classify_it PASSED
tests/test_triage.py::test_classify_vague_defaults_to_general PASSED
tests/test_triage.py::test_classify_returns_all_fields PASSED
tests/test_triage.py::test_classify_priority_values PASSED
tests/test_triage.py::test_classify_category_values PASSED
tests/test_triage.py::test_classify_case_insensitive PASSED
tests/test_triage.py::test_recommended_action_not_empty PASSED
tests/test_api.py::test_create_request_success PASSED
tests/test_api.py::test_create_request_auto_classifies PASSED
tests/test_api.py::test_create_request_missing_description PASSED
tests/test_api.py::test_create_request_missing_location PASSED
tests/test_api.py::test_create_request_default_status PASSED
tests/test_api.py::test_get_all_requests_empty PASSED
tests/test_api.py::test_get_all_requests_returns_list PASSED
tests/test_api.py::test_get_requests_filter_by_category PASSED
tests/test_api.py::test_get_requests_filter_by_status PASSED
tests/test_api.py::test_get_single_request PASSED
tests/test_api.py::test_get_request_not_found PASSED
tests/test_api.py::test_update_status_success PASSED
tests/test_api.py::test_update_status_resolved PASSED
tests/test_api.py::test_update_status_invalid PASSED
tests/test_api.py::test_update_status_not_found PASSED
tests/test_api.py::test_health_check PASSED
tests/test_api.py::test_root_endpoint PASSED

========= 31 passed in 1.45s =========
```

---

## Folder Structure After Day 3

```
city-service-triage-agent/
├── backend/
│   ├── venv/
│   ├── database.db
│   ├── database.py
│   ├── models.py
│   ├── schemas.py
│   ├── triage.py
│   ├── main.py
│   └── tests/
│       ├── __init__.py           ← NEW: makes tests a package
│       ├── test_triage.py        ← NEW: 13 classifier tests
│       └── test_api.py           ← NEW: 18 API endpoint tests
├── frontend/
│   └── index.html
├── mcp/
│   ├── service_request_tools.py
│   └── test_mcp.py
├── docs/
│   └── 09_week3_day3_pytest.md  ← this file
└── .gitignore
```

---

## Interview Prep

### Unit test vs integration test?

Unit tests test one function in isolation — no database, no HTTP. The triage tests are unit tests: they call `classify_request()` directly and check the return value.

Integration tests test multiple components working together. The API tests are integration tests: they send HTTP requests that go through FastAPI routing, validation, database operations, and the classifier — the full stack.

### Why in-memory database for tests?

Using the real `database.db` would mean tests leave data behind, tests could interfere with each other, and tests would fail if the database had unexpected data from previous runs. An in-memory database gives each test run a clean slate and is destroyed automatically when the test ends.

### What does a fixture do?

A fixture is a setup function that runs before each test that requests it. `session_fixture` creates a fresh in-memory database. `client_fixture` takes that session, tells FastAPI to use it instead of the real session, creates a test client, and cleans up after the test. Fixtures keep test setup code out of the test functions themselves.

### Why does missing description return 422?

FastAPI automatically validates request bodies against the schema. `ServiceRequestCreate` requires `description: str`. If the field is missing, FastAPI returns 422 Unprocessable Entity before your function even runs. You never write validation code for this — FastAPI handles it automatically.

### What does dependency_overrides do?

It replaces a dependency with a different implementation for the duration of the test. The real `get_session` opens a connection to `database.db`. The override returns a session connected to the in-memory test database instead. After the test, `.clear()` removes the override so the real dependency is restored.

---

## Git Commit — End of Day 3

```bash
cd ~/Desktop/city-service-triage-agent
git add .
git commit -m "Week 3 Day 3: pytest tests for classifier and API endpoints"
git push
```

---

## Next Step

→ **Week 3 Day 4:** Write the four required submission documents —
business statement, logical structure, technical implementation guide,
and agent regeneration blueprint.

---

*Project: City Service Triage Agent*
*Internship: City of Los Angeles — Department of General Services*
*Week 3 Day 3 — pytest Tests*
