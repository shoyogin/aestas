"""Shared FastAPI dependencies (e.g. get_current_user)."""
from fastapi import Depends, HTTPException, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.session import get_session


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
) -> User:
    """Dependency: require a valid session and return the User."""
    session_data = get_session(request.cookies.get("session"))
    if not session_data:
        raise HTTPException(status_code=401, detail="Not authenticated")
    user = db.query(User).filter(User.id == session_data["user_id"]).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user
