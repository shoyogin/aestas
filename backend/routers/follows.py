"""Consent-based follows: friend vs partner."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import func
from sqlalchemy.orm import Session

from cycle_phase import get_phase_for_today
from database import get_db
from dependencies import get_current_user
from models import FollowRequest, User
from phase_share import PHASE_LABELS, panels_for_link

router = APIRouter()

LINK_TYPES = {"friend", "partner"}
PENDING_TTL_DAYS = 14


class FollowCreateBody(BaseModel):
    nickname: str = Field(..., min_length=1, max_length=24)
    link_type: str = Field(..., description="friend | partner")


def _serialize(row: FollowRequest, other: User | None, *, as_inbox: bool) -> dict:
    return {
        "id": row.id,
        "link_type": row.link_type,
        "status": row.status,
        "nickname": other.nickname if other else None,
        "created_at": row.created_at.isoformat() if row.created_at else None,
        "direction": "incoming" if as_inbox else "outgoing",
    }


def _other_user(db: Session, row: FollowRequest, me: User) -> User | None:
    oid = row.requester_id if row.target_id == me.id else row.target_id
    return db.query(User).filter(User.id == oid).first()


def _pending_cutoff():
    return datetime.now(timezone.utc) - timedelta(days=PENDING_TTL_DAYS)


@router.post("")
def create_follow(
    body: FollowCreateBody,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    if body.link_type not in LINK_TYPES:
        raise HTTPException(status_code=400, detail="link_type must be friend or partner")
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
        return _serialize(existing, target, as_inbox=False)

    row = FollowRequest(
        requester_id=current_user.id,
        target_id=target.id,
        link_type=body.link_type,
        status="pending",
    )
    db.add(row)
    db.commit()
    db.refresh(row)
    return _serialize(row, target, as_inbox=False)


@router.get("/inbox")
def inbox(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    cutoff = _pending_cutoff()
    rows = (
        db.query(FollowRequest)
        .filter(
            FollowRequest.target_id == current_user.id,
            FollowRequest.status == "pending",
            FollowRequest.created_at >= cutoff,
        )
        .order_by(FollowRequest.created_at.desc())
        .all()
    )
    out = []
    for row in rows:
        other = db.query(User).filter(User.id == row.requester_id).first()
        out.append(_serialize(row, other, as_inbox=True))
    return out


@router.get("")
def list_following(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    rows = (
        db.query(FollowRequest)
        .filter(
            FollowRequest.requester_id == current_user.id,
            FollowRequest.status == "accepted",
        )
        .order_by(FollowRequest.updated_at.desc())
        .all()
    )
    out = []
    for row in rows:
        other = db.query(User).filter(User.id == row.target_id).first()
        item = _serialize(row, other, as_inbox=False)
        if other:
            info = get_phase_for_today(
                other.cycle_length,
                list(other.cycle_start_dates or []),
                list(other.cycle_end_dates or []),
            )
            item["phase"] = info["phase"]
            item["cycle_day"] = info["cycle_day"]
            item["phase_label"] = PHASE_LABELS.get(info["phase"]) if info["phase"] else None
        else:
            item["phase"] = None
            item["cycle_day"] = None
            item["phase_label"] = None
        out.append(item)
    return out


def _get_row(db: Session, follow_id: int) -> FollowRequest:
    row = db.query(FollowRequest).filter(FollowRequest.id == follow_id).first()
    if not row:
        raise HTTPException(status_code=404, detail="Request not found.")
    return row


@router.post("/{follow_id}/accept")
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
    other = db.query(User).filter(User.id == row.requester_id).first()
    return _serialize(row, other, as_inbox=True)


@router.post("/{follow_id}/refuse")
def refuse_follow(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_row(db, follow_id)
    if row.target_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not your inbox.")
    if row.status != "pending":
        raise HTTPException(status_code=409, detail="This request is not pending.")
    row.status = "refused"
    db.commit()
    return {"ok": True}


@router.delete("/{follow_id}")
def revoke_follow(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_row(db, follow_id)
    if current_user.id not in (row.requester_id, row.target_id):
        raise HTTPException(status_code=403, detail="Not your follow.")
    row.status = "revoked"
    db.commit()
    return {"ok": True}


@router.get("/{follow_id}/cycle")
def shared_cycle(
    follow_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    row = _get_row(db, follow_id)
    if row.requester_id != current_user.id:
        raise HTTPException(status_code=403, detail="Only the follower can view this.")
    if row.status != "accepted":
        raise HTTPException(status_code=404, detail="Not connected.")
    target = db.query(User).filter(User.id == row.target_id).first()
    if not target:
        raise HTTPException(status_code=404, detail="User not found.")
    info = get_phase_for_today(
        target.cycle_length,
        list(target.cycle_start_dates or []),
        list(target.cycle_end_dates or []),
    )
    phase = info["phase"]
    return {
        "nickname": target.nickname,
        "link_type": row.link_type,
        "phase": phase,
        "cycle_day": info["cycle_day"],
        "phase_label": PHASE_LABELS.get(phase) if phase else None,
        "panels": panels_for_link(phase, row.link_type),
        "disclaimer": "They share cycle phase only — not flow or exact dates. Educational, not medical advice.",
    }
