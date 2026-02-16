"""User-related endpoints (onboarding, etc.)."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database import get_db
from models import User
from dependencies import get_current_user

router = APIRouter()


class OnboardingBody(BaseModel):
    cycle_length: int = Field(..., ge=21, le=45, description="Typical cycle length in days")


@router.post("/onboarding")
def post_onboarding(
    body: OnboardingBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Save the user's cycle length (onboarding)."""
    current_user.cycle_length = body.cycle_length
    db.commit()
    db.refresh(current_user)
    return {"ok": True, "cycle_length": current_user.cycle_length}
