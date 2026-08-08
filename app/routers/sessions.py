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
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
):
    new_session = Session(goal=payload.goal)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)

    memory_context = await get_relevent_memory(db, payload.goal)
    prompt = payload.goal
    if memory_context:
        prompt = f"Relevant past context: {memory_context}\n\nCurrent goal: {payload.goal}"

    result_text = await call_llm(prompt)

    step = AgentStep(
        session_id = new_session.id,
        role = AgentRole.EXECUTOR,
        step_number = 1,
        input = {"goal": new_session.goal, "prompt_sent": prompt},
        output = {"response":result_text},
        status = StepStatus.COMPLETED,
    )
    db.add(step)

    embedding_vector = await get_embedding(new_session.goal)
    memory = MemoryEntry(
        content=new_session.goal,
        embedding=embedding_vector,
    )
    db.add(memory)

    new_session.status = SessionStatus.DONE
    await db.commit()
    await db.refresh(new_session)

    return new_session

