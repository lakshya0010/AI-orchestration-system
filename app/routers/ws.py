import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.session import Session

router = APIRouter()

@router.websocket("/ws/{session_id}")
async def session_websocket(websocket: WebSocket, session_id: str):
    await websocket.accept()

    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Session).where(Session.id == uuid.UUID(session_id))
        )
        session = result.scalar_one_or_none()

    if session is None:
        await websocket.send_json({
            "event": "error",
            "message": "Session not found"
        })
        await websocket.close()
        return

    await websocket.send_json({
        "event": "connected",
        "session_id": str(session_id),
        "goal": session.goal,
        "status": session.status.value,
    })

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        pass
    


