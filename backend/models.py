from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, Field


class ServiceRequest(SQLModel, table=True):
    """
    Represents one citizen service request in the database.
    Each instance of this class = one row in the servicerequest table.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    # Optional means it can be None — SQLite assigns the actual number automatically

    description: str
    # The text the citizen typed — what is the problem?

    location: str
    # Where is the problem? (street address, intersection, landmark)

    category: Optional[str] = Field(default=None)
    # Assigned by the triage classifier later — not filled in by the user
    # Options: maintenance, safety, sanitation, facility, IT

    priority: Optional[str] = Field(default=None)
    # Assigned by the triage classifier later
    # Options: low, medium, high, critical

    status: str = Field(default="open")
    # Lifecycle state of the request
    # Starts as "open", can become "in_progress" or "resolved"

    created_at: datetime = Field(default_factory=datetime.utcnow)
    # Timestamp set automatically when the row is created
    # utcnow() means "current time in UTC" — standard for server timestamps