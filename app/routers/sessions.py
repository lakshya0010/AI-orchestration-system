from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from app.database import get_db
from app.models.session import Session, SessionStatus
from app.schemas.session import SessionCreate, SessionResponse
from app.models.agent_step import AgentRole, AgentStep, StepStatus
from app.services.llm import call_llm

router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
):
    new_session = Session(goal=payload.goal)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    result_text = await call_llm(new_session.goal)

    step = AgentStep(
        session_id = new_session.id,
        role = AgentRole.EXECUTOR,
        step_number = 1,
        input = {"goal":new_session.goal},
        output = {"response":result_text},
        status = StepStatus.COMPLETED,
    )
    db.add(step)

    new_session.status = SessionStatus.DONE
    await db.commit()
    await db.refresh(new_session)

    return new_session

