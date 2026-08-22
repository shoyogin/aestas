"""Static educational copy, served so the frontend never keeps a second copy."""
from fastapi import APIRouter, Depends

from app.dependencies import get_current_user
from app.phase_content import owner_content
from app.schemas import PhaseContentResponse

router = APIRouter()


@router.get(
    "/phases",
    response_model=PhaseContentResponse,
    # Nothing here is secret, but nothing in this app is public either.
    dependencies=[Depends(get_current_user)],
)
def get_phase_content():
    """Labels, panel order, and the full per-phase panels for the owner's own view."""
    return PhaseContentResponse(**owner_content())
