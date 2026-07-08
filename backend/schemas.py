from typing import Optional
from sqlmodel import SQLModel


class ServiceRequestCreate(SQLModel):
    """
    Defines what data the API accepts when creating a new request.
    Only description and location — the citizen fills these in.
    Everything else (category, priority, status, created_at) is
    assigned automatically by the system.
    """
    description: str
    location: str


class ServiceRequestRead(SQLModel):
    """
    Defines what data the API returns when reading a request.
    Includes all fields including the ones the system assigned.
    This is what the frontend and dashboard will display.
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