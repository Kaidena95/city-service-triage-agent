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
    """Runs on startup — creates DB tables if they don't exist."""
    create_db_and_tables()
    yield


app = FastAPI(lifespan=lifespan)

# CORS — allows the frontend HTML file to call this API
# Without this the browser blocks all requests from the frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Health check ───────────────────────────────
@app.get("/")
def read_root():
    return {"message": "City Service Triage API is running"}


@app.get("/health")
def health_check():
    return {"status": "ok"}


# ── Create a new service request ───────────────
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


# ── Get all service requests ───────────────────
@app.get("/requests", response_model=List[ServiceRequestRead])
def get_all_requests(session: Session = Depends(get_session)):
    requests = session.exec(select(ServiceRequest)).all()
    return requests


# ── Get one service request by ID ─────────────
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