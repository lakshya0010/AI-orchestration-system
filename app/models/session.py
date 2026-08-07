import uuid
import enum
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.dialects.postgresql import UUID, ENUM as PgEnum
from sqlalchemy.orm import Mapped, mapped_column
from app.database import Base

class SessionStatus(str, enum.Enum):
    PLANNING = "planning"
    EXECUTING = "executing"
    CRITIQUING = "critiquing"
    REPLANNING = "replanning"
    DONE = "done"
    FAILED = "failed"

class Session(Base):
    __tablename__ = "sessions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    goal: Mapped[str] = mapped_column(
        String, nullable=False
    )
    status: Mapped[SessionStatus] = mapped_column(
        PgEnum(SessionStatus, name="session_status"),
        nullable=False,
        default=SessionStatus.PLANNING
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

