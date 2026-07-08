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


# ─────────────────────────────────────────────
# ENDPOINT 1 — Health check
# ─────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ─────────────────────────────────────────────
# ENDPOINT 2 — Create a new service request
# Method: POST
# URL: /requests
# Body: { "description": "...", "location": "..." }
# Returns: the full saved request including id and timestamps
# ─────────────────────────────────────────────
@app.post("/requests", response_model=ServiceRequestRead)
def create_request(
    request_data: ServiceRequestCreate,
    session: Session = Depends(get_session)
):
    """
    Accepts a new service request from the frontend form.
    Saves it to the database and returns the saved record.
    Category and priority are None for now — the triage
    classifier (Day 3 Week 2) will fill these in later.
    """
    # Create a ServiceRequest database object from the incoming data
    db_request = ServiceRequest(
        description=request_data.description,
        location=request_data.location
    )

    # Add to session (staged for saving)
    session.add(db_request)

    # Commit — actually writes to database.db
    session.commit()

    # Refresh — reloads the object from DB so we get the auto-assigned id
    session.refresh(db_request)

    return db_request


# ─────────────────────────────────────────────
# ENDPOINT 3 — Get all service requests
# Method: GET
# URL: /requests
# Returns: list of all requests in the database
# ─────────────────────────────────────────────
@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(session: Session = Depends(get_session)):
    """
    Returns every service request stored in the database.
    The dashboard will call this to display all requests.
    """
    requests = session.exec(select(ServiceRequest)).all()
    return requests


# ─────────────────────────────────────────────
# ENDPOINT 4 — Get one service request by ID
# Method: GET
# URL: /requests/{id}  (example: /requests/1)
# Returns: one request, or 404 if not found
# ─────────────────────────────────────────────
@app.get("/requests/{request_id}", response_model=ServiceRequestRead)
def get_request(
    request_id: int,
    session: Session = Depends(get_session)
):
    """
    Returns one specific service request by its ID.
    If the ID doesn't exist in the database, returns a 404 error.
    """
    db_request = session.get(ServiceRequest, request_id)

    if not db_request:
        raise HTTPException(
            status_code=404,
            detail=f"Request with id {request_id} not found"
        )

    return db_request