from typing import Optional
from sqlmodel import SQLModel


class ServiceRequestCreate(SQLModel):
    """
    What the API accepts when creating a new request.
    Only citizen-provided fields.
    """
    description: str
    location: str


class ServiceRequestRead(SQLModel):
    """
    What the API returns when reading a request.
    Includes all fields — citizen input + system assigned.
    """
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
        