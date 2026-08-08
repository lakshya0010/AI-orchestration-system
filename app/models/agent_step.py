import uuid
import enum
from datetime import datetime
from sqlalchemy import ForeignKey, String, Integer, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB, ENUM as PgEnum
from app.database import Base

class AgentRole(str, enum.Enum):
    PLANNER = "planner"
    EXECUTOR = "executor"
    CRITIC = "critic"

class StepStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"

class AgentStep(Base):
    __tablename__ = "agent_steps"
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    session_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("sessions.id"), nullable=False
    )
    role: Mapped[AgentRole] = mapped_column(
        PgEnum(AgentRole, name="agent_role"), nullable=False
    )
    step_number: Mapped[int] = mapped_column(Integer, nullable=False)
    input: Mapped[dict] = mapped_column(JSONB, nullable=True)
    output: Mapped[dict] = mapped_column(JSONB, nullable=True)
    status: Mapped[StepStatus] = mapped_column(
        PgEnum(StepStatus, name="step_status"),
        nullable=False,
        default=StepStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), server_default=func.now()
    )