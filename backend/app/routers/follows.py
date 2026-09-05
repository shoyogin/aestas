"""Consent-based follows: friend vs partner.

Lifecycle follows the Instagram model. A request sits pending until the target
acts on it; until then the only thing the requester can do is withdraw it and
send it again. Refused, withdrawn, and revoked edges are all re-requestable, so
the row is reused rather than duplicated (uq_follow_requester_target).
"""
import logging

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.avatars import avatar_version
from app.config import settings
from app.cycle_phase import get_phase_for_today
from app.database import get_db
from app.dependencies import get_current_user
from app.models import LINK_TYPES, FollowRequest, User
from app.phase_content import panels_for_link, shared_disclaimer
from app.ratelimit import rate_limit
from app.schemas import (
    FollowCreateBody,
    FollowSummary,
    FollowWithPhase,
    OkResponse,
    SharedCycleResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter()

# Statuses a requester may re-request from.
REREQUESTABLE = ("refused", "revoked", "withdrawn")

follow_write_limit = Depends(
    rate_limit("follow_write", settings.rate_limit_follow_write)
)


def _summary(row: FollowRequest, other: User | None, *, direction: str) -> FollowSummary:
    return FollowSummary(
        id=row.id,
        link_type=row.link_type,
        status=row.status,
        nickname=other.nickname if other else None,
        created_at=row.created_at.isoformat() if row.created_at else None,
        direction=direction,
        avatar_updated_at=avatar_version(other),
    )


def _with_phase(row: FollowRequest, other: User | None) -> FollowWithPhase:
    base = _summary(row, other, direction="outgoing").model_dump()
    info = (
        get_phase_for_today(
            other.cycle_length,
            list(other.cycle_start_dates or []),
            list(other.cycle_end_dates or []),
            other.timezone,
        )
        if other
        else {"phase": None, "cycle_day": None, "phase_label": None}
    )
    return FollowWithPhase(**base, **info)


def _get_row(db: Session, follow_id: int) -> FollowRequest:
    row = (
        db.query(FollowRequest)
        .options(
            joinedload(FollowRequest.requester).joinedload(User.profile_picture),
            joinedload(FollowRequest.target).joinedload(User.profile_picture),
        )
        .filter(FollowRequest.id == follow_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Request not found.")
    return row


@router.post("", response_model=FollowSummary, dependencies=[follow_write_limit])
def create_follow(
    body: FollowCreateBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Send a follow request, or re-send one that was refused/withdrawn/revoked."""
    if body.link_type not in LINK_TYPES:
        raise HTTPException(
            status_code=400, detail=f"link_type must be one of: {', '.join(LINK_TYPES)}"
        )
    nick = body.nickname.strip().lower()
    target = db.query(User).filter(func.lower(User.nickname) == nick).first()
    if not target:
        raise HTTPException(status_code=404, detail="No one with that nickname.")
    if target.id == current_user.id:
        raise HTTPException(status_code=400, detail="You cannot follow yourself.")

    existing = (
        db.query(FollowRequest)
        .filter(
            FollowRequest.requester_id == current_user.id,
            FollowRequest.target_id == target.id,
        )
        .first()
    )
    if existing:
        if existing.status == "accepted":
            raise HTTPException(status_code=409, detail="You already follow them.")
        if existing.status == "pending":
            raise HTTPException(status_code=409, detail="Request already pending.")
        existing.link_type = body.link_type
        existing.status = "pending"
        db.commit()
        db.refresh(existing)
        return _summary(existing, target, direction="outgoing")

    row = FollowRequest(
        requester_id=current_user.id,
        target_id=target.id,
        link_type=body.link_type,
        status="pending",
    )
    db.add(row)
    try:
        db.commit()
    except IntegrityError as err:
        # Two taps on "Send request" racing each other.
        db.rollback()
        raise HTTPException(status_code=409, detail="Request already pending.") from err
    db.refresh(row)
    return _summary(row, target, direction="outgoing")


@router.get("/inbox", response_model=list[FollowSummary])
def inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Requests waiting on me. Pending requests never expire; the requester
    withdraws them instead, so nothing can get stuck invisible-but-blocking."""
    rows = (
        db.query(FollowRequest)
        .options(joinedload(FollowRequest.requester).joinedload(User.profile_picture))
        .filter(
            FollowRequest.target_id == current_user.id,
            FollowRequest.status == "pending",
        )
        .order_by(FollowRequest.created_at.desc())
        .all()
    )
    return [_summary(row, row.requester, direction="incoming") for row in rows]


@router.get("", response_model=list[FollowWithPhase])
def list_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """People I follow, with the phase they have agreed to share."""
    rows = (
        db.query(FollowRequest)
        .options(joinedload(FollowRequest.target).joinedload(User.profile_picture))
        .filter(
            FollowRequest.requester_id == current_user.id,
            FollowRequest.status == "accepted",
        )
        .order_by(FollowRequest.updated_at.desc())
        .all()
    )
    return [_with_phase(row, row.target) for row in rows]


@router.get("/requests", response_model=list[FollowSummary])
def list_outgoing_requests(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Requests I have sent that are still pending, so the UI can offer to
    cancel them (the only action available before the target accepts)."""
    rows = (
        db.query(FollowRequest)
        .options(joinedload(FollowRequest.target).joinedload(User.profile_picture))
        .filter(
            FollowRequest.requester_id == current_user.id,
            FollowRequest.status == "pending",
        )
        .order_by(FollowRequest.created_at.desc())
        .all()
    )
    return [_summary(row, row.target, direction="outgoing") for row in rows]


@router.get("/followers", response_model=list[FollowSummary])
def list_followers(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """People who can see my phase, so access I granted can be taken back."""
    rows = (
        db.query(FollowRequest)
        .options(joinedload(FollowRequest.requester).joinedload(User.profile_picture))
        .filter(
            FollowRequest.target_id == current_user.id,
            FollowRequest.status == "accepted",
        )
        .order_by(FollowRequest.updated_at.desc())
        .all()
    )
    return [_summary(row, row.requester, direction="incoming") for row in rows]


@router.post("/{follow_id}/accept", response_model=FollowSummary, dependencies=[follow_write_limit])
def accept_follow(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_row(db, follow_id)
    if row.target_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your inbox.")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="This request is not pending.")
    if row.link_type == "partner":
        other_partner = (
            db.query(FollowRequest)
            .filter(
                FollowRequest.target_id == current_user.id,
                FollowRequest.link_type == "partner",
                FollowRequest.status == "accepted",
                FollowRequest.id != row.id,
            )
            .first()
        )
        if other_partner:
            raise HTTPException(
                status_code=409,
                detail="You already have a partner follow. Revoke it first.",
            )
    row.status = "accepted"
    db.commit()
    db.refresh(row)
    logger.info("Follow %s accepted by user %s", row.id, current_user.id)
    return _summary(row, row.requester, direction="incoming")


@router.post("/{follow_id}/refuse", response_model=OkResponse, dependencies=[follow_write_limit])
def refuse_follow(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Decline a request. The requester may send a new one later."""
    row = _get_row(db, follow_id)
    if row.target_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your inbox.")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="This request is not pending.")
    row.status = "refused"
    db.commit()
    return OkResponse()


@router.delete("/{follow_id}", response_model=OkResponse, dependencies=[follow_write_limit])
def delete_follow(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Withdraw my pending request, unfollow, or remove one of my followers."""
    row = _get_row(db, follow_id)
    is_requester = row.requester_id == current_user.id
    is_target = row.target_id == current_user.id
    if not (is_requester or is_target):
        raise HTTPException(status_code=403, detail="Not your follow.")

    if row.status == "pending":
        if not is_requester:
            # The target declines rather than withdraws; keep the two distinct.
            raise HTTPException(
                status_code=409, detail="Refuse this request instead of removing it."
            )
        row.status = "withdrawn"
    elif row.status == "accepted":
        row.status = "revoked"
    else:
        raise HTTPException(status_code=409, detail="This follow is not active.")

    db.commit()
    logger.info("Follow %s set to %s by user %s", row.id, row.status, current_user.id)
    return OkResponse()


@router.get("/{follow_id}/cycle", response_model=SharedCycleResponse)
def shared_cycle(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """The phase and advice a single follower is entitled to see."""
    row = _get_row(db, follow_id)
    if row.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the follower can view this.")
    if row.status != "accepted":
        raise HTTPException(status_code=404, detail="Not connected.")
    target = row.target
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    info = get_phase_for_today(
        target.cycle_length,
        list(target.cycle_start_dates or []),
        list(target.cycle_end_dates or []),
        target.timezone,
    )
    return SharedCycleResponse(
        nickname=target.nickname,
        link_type=row.link_type,
        avatar_updated_at=avatar_version(target),
        phase=info["phase"],
        cycle_day=info["cycle_day"],
        phase_label=info["phase_label"],
        panels=panels_for_link(info["phase"], row.link_type),
        disclaimer=shared_disclaimer(),
    )
