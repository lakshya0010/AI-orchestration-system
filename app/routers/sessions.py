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

router = APIRouter()

async def get_relevent_memory(db: DBSession, query_text:str)->str | None:
    query_embedding = await get_embedding(query_text)
    result = await db.execute(
        select(MemoryEntry).order_by(MemoryEntry.embedding.cosine_distance(query_embedding)).limit(1)
    )
    match = result.scalar_one_or_none()
    return match.content if match else None

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

