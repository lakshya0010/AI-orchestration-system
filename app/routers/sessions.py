from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession as DBSession
from app.database import get_db
from app.models.session import Session
from app.schemas.session import SessionCreate, SessionResponse

router = APIRouter()

@router.get("", response_model=SessionResponse)
async def create_session(
    payload: SessionCreate,
    db: DBSession = Depends(get_db),
):
    new_session = Session(goal=payload.goal)
    db.add(new_session)
    await db.commit()
    await db.refresh(new_session)
    return new_session

