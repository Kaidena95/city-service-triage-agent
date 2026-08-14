from contextlib import asynccontextmanager
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select
from database import create_db_and_tables, get_session
from models import ServiceRequest
from schemas import ServiceRequestCreate, ServiceRequestRead
from triage import classify_request


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Runs on startup — creates DB tables if they don't exist."""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# CORS middleware — allows browser requests from frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health checks ──────────────────────────────────────────────────
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── Create a new service request ───────────────────────────────────
@app.post("/requests", response_model=ServiceRequestRead)
def create_request(
    request_data: ServiceRequestCreate,
    session: Session = Depends(get_session)
):
    """
    Accepts a new service request from the frontend form.
    Automatically runs the triage classifier on the description.
    Stores category, priority, and recommended_action in the DB.
    """
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


# ── Get all service requests with optional filters ─────────────────
@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(
    session: Session = Depends(get_session),
    category: Optional[str] = Query(default=None),
    priority: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None)
):
    """
    Returns service requests from the database.
    Supports optional query parameter filters:
      GET /requests                        → all requests
      GET /requests?category=maintenance   → filtered by category
      GET /requests?priority=high          → filtered by priority
      GET /requests?status=open            → filtered by status
      GET /requests?category=safety&status=open → combined filters
    """
    query = select(ServiceRequest)

    # Apply filters only if the parameter was provided
    if category:
        query = query.where(ServiceRequest.category == category)
    if priority:
        query = query.where(ServiceRequest.priority == priority)
    if status:
        query = query.where(ServiceRequest.status == status)

    requests = session.exec(query).all()
    return requests


# ── Get one service request by ID ──────────────────────────────────
@app.get("/requests/{request_id}", response_model=ServiceRequestRead)
def get_request(
    request_id: int,
    session: Session = Depends(get_session)
):
    """Returns one request by ID. Returns 404 if not found."""
    db_request = session.get(ServiceRequest, request_id)
    if not db_request:
        raise HTTPException(
            status_code=404,
            detail=f"Request with id {request_id} not found"
        )
    return db_request


# ── Update request status ──────────────────────────────────────────
@app.patch("/requests/{request_id}/status")
def update_status(
    request_id: int,
    status: str,
    session: Session = Depends(get_session)
):
    """
    Updates only the status field of a request.
    Valid values: open, in_progress, resolved
    Uses PATCH because only one field is being updated.
    PUT would require sending all fields.
    """
    valid_statuses = ["open", "in_progress", "resolved"]
    if status not in valid_statuses:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid status. Must be one of: {valid_statuses}"
        )

    db_request = session.get(ServiceRequest, request_id)
    if not db_request:
        raise HTTPException(
            status_code=404,
            detail=f"Request with id {request_id} not found"
        )

    db_request.status = status
    session.add(db_request)
    session.commit()
    session.refresh(db_request)
    return db_request