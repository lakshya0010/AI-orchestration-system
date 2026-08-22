from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from app.database import get_db
from app.models.session import Session, SessionStatus
from app.schemas.session import SessionCreate, SessionResponse
from app.models.agent_step import AgentRole, AgentStep, StepStatus
from app.services.llm import call_llm
from app.models.memory_entry import MemoryEntry
from app.services.embeddings import get_embedding
from sqlalchemy import select
from fastapi import BackgroundTasks
from app.services.orchestrator import run_orchestrator
from sqlalchemy.orm import selectinload
import uuid
from fastapi import HTTPException

router = APIRouter()

@router.post("", response_model=SessionResponse)
async def create_session(
    background_tasks: BackgroundTasks,
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
):
    new_session = Session(goal=payload.goal)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    background_tasks.add_task(run_orchestrator, new_session.id)
    
    return new_session

@router.post("/{session_id}/answer")
async def answer_session(
    session_id: uuid.UUID,
    payload: dict,
    background_tasks: BackgroundTasks,
    db:DBSession = Depends(get_db),
    ):
    result = await db.execute(select(Session).where(Session.id == session_id))
    session = result.scalar_one_or_none()
    if session is None or session.status != SessionStatus.AWAITING_INPUT:
        raise HTTPException(status_code=400, detail="session not awaiting input")

    session.goal = f"{session.goal}\n\nAdditional info from user: {payload['answer']}"
    session.status = SessionStatus.PLANNING
    await db.commit()

    background_tasks.add_task(run_orchestrator, session.id)
    return {"status": "resumed"}
    


@router.get("/{session_id}")
async def get_session(session_id: uuid.UUID, db:DBSession = Depends(get_db)):
    result = await db.execute(
        select(Session).where(Session.id == session_id)
    )
    session = result.scalar_one_or_none()
    if session is None:
        raise HTTPException(status_code=404, detail="session not found")

    steps_result = await db.execute(
        select(AgentStep).where(AgentStep.session_id == session_id)
        .order_by(AgentStep.step_number)
    )
    steps = steps_result.scalars().all()

    return{
        "id":session.id,
        "goal":session.goal,
        "status":session.status,
        "steps":[
            {
                "step_number":s.step_number,
                "role":s.role.value,
                "input":s.input,
                "output":s.output,
                "status":s.status.value,
            }
            for s in steps
        ],
    }
