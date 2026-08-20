from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ServiceRequest(SQLModel, table=True):
    """
    Database table definition for service requests.
    Each instance = one row in the servicerequest table.
    """
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

    