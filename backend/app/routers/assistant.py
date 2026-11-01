"""Personal AI career assistant (chat), grounded in the student's own data."""
from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import ChatMessage, User
from app.ratelimit import limiter
from app.schemas import ChatIn
from app.security import get_current_user
from app.services import assistant

router = APIRouter(prefix="/api/assistant", tags=["assistant"])


def msg_out(m: ChatMessage) -> dict:
    return {"id": m.id, "role": m.role, "content": m.content, "meta": m.meta, "at": m.created_at.isoformat()}


@router.get("")
def history(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    rows = db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.id)).all()
    return [msg_out(m) for m in rows[-50:]]


@router.post("", dependencies=[Depends(limiter("ai"))])
def ask(body: ChatIn, user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    past = db.scalars(select(ChatMessage).where(ChatMessage.user_id == user.id).order_by(ChatMessage.id.desc()).limit(8)).all()
    hist = [{"role": m.role, "content": m.content} for m in reversed(past)]
    db.add(ChatMessage(user_id=user.id, role="user", content=body.message))
    result = assistant.answer(db, user.id, body.message, hist)
    reply = ChatMessage(user_id=user.id, role="assistant", content=result["content"],
                        meta={"citations": result["citations"], "engine": result["engine"], "ai_error": result.get("ai_error")})
    db.add(reply)
    db.commit()
    return msg_out(reply)


@router.delete("")
def clear(user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    db.query(ChatMessage).filter(ChatMessage.user_id == user.id).delete()
    db.commit()
    return {"ok": True}
