from pydantic import BaseModel
import uuid
from datetime import datetime
from app.models.session import SessionStatus

class SessionCreate(BaseModel):
    goal: str

class SessionResponse(BaseModel):
    id:uuid.UUID
    goal: str
    status: SessionStatus
    created_at: datetime

    model_config = {"from_attributes":True}

    