"""Profile pictures: upload, remove, and serve.

Mounted under /users, so the routes read /users/me/avatar and
/users/{nickname}/avatar.

Who may see whose picture follows the rule the rest of the app already uses:
you can see someone's avatar exactly when a follow edge exists between you,
pending or accepted, in either direction — the same set of people the Circle
screen already shows you by nickname. Search results are deliberately outside
that set, so a stranger cannot walk the nickname space collecting faces.
"""
import logging

from fastapi import APIRouter, Depends, File, HTTPException, Request, Response, UploadFile
from sqlalchemy import func, or_, select
from sqlalchemy.orm import Session

from app.avatars import AVATAR_CONTENT_TYPE, AvatarError, normalize_avatar
from app.config import settings
from app.database import get_db
from app.dependencies import get_current_user
from app.models import FollowRequest, ProfilePicture, User
from app.ratelimit import rate_limit
from app.schemas import AvatarResponse, OkResponse

logger = logging.getLogger(__name__)

router = APIRouter()

# Statuses that make two people visible to each other. "pending" is in the list
# so the inbox can show a face beside a request you have not answered yet.
VISIBLE_LINK_STATUSES = ("pending", "accepted")

UPLOAD_CHUNK = 64 * 1024
# Multipart framing (boundaries, the part headers, the filename) adds a few
# hundred bytes to the body. This is the slack allowed for it when judging a
# declared Content-Length, generous enough never to refuse a legitimate upload.
MULTIPART_SLACK = 64 * 1024

avatar_write_limit = Depends(rate_limit("avatar_write", settings.rate_limit_avatar_write))


def _too_large() -> HTTPException:
    megabytes = settings.avatar_max_upload_bytes / (1024 * 1024)
    return HTTPException(
        status_code=413, detail=f"That image is too big. The limit is {megabytes:.0f} MB."
    )


async def _read_capped(upload: UploadFile) -> bytes:
    """Read the upload, stopping as soon as it exceeds the configured limit.

    This is what bounds the bytes held in memory and handed to the decoder.
    Starlette has already parsed the multipart body by the time we get here —
    spooling it to a temporary file past a megabyte — so the Content-Length
    check in the handler is what keeps an absurd body from being buffered at
    all; between them, neither an honest nor a silent client gets far.
    """
    limit = settings.avatar_max_upload_bytes
    chunks: list[bytes] = []
    total = 0
    while chunk := await upload.read(UPLOAD_CHUNK):
        total += len(chunk)
        if total > limit:
            raise _too_large()
        chunks.append(chunk)
    return b"".join(chunks)


def _etag(version: str) -> str:
    """A picture is immutable for as long as its updated_at is unchanged."""
    return f'"{version}"'


def _picture_or_404(db: Session, user_id: int) -> ProfilePicture:
    row = db.execute(
        select(ProfilePicture).where(ProfilePicture.user_id == user_id)
    ).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="No profile picture.")
    return row


def _image_response(request: Request, row: ProfilePicture) -> Response:
    """Serve the bytes, or a 304 when the browser already has this version.

    `data` is a deferred column, so a revalidation that ends in 304 never reads
    the image out of the database at all.
    """
    version = row.updated_at.isoformat() if row.updated_at else ""
    etag = _etag(version)
    headers = {
        "ETag": etag,
        # Private: this is one signed-in user's view of another's picture, and
        # no shared cache should hold it. must-revalidate keeps a changed
        # picture from lingering, and the ETag makes that check cheap.
        "Cache-Control": "private, max-age=0, must-revalidate",
        # The stored bytes are always WebP, but say so out loud: no sniffing.
        "X-Content-Type-Options": "nosniff",
        "Content-Disposition": "inline",
    }
    if request.headers.get("if-none-match") == etag:
        return Response(status_code=304, headers=headers)
    return Response(content=row.data, media_type=row.content_type, headers=headers)


def _may_see(db: Session, viewer: User, target: User) -> bool:
    if viewer.id == target.id:
        return True
    link = db.execute(
        select(FollowRequest.id)
        .where(
            or_(
                (FollowRequest.requester_id == viewer.id)
                & (FollowRequest.target_id == target.id),
                (FollowRequest.requester_id == target.id)
                & (FollowRequest.target_id == viewer.id),
            ),
            FollowRequest.status.in_(VISIBLE_LINK_STATUSES),
        )
        .limit(1)
    ).first()
    return link is not None


# "me" is shorter than the 3-character nickname minimum, so it can never be
# someone's name — but this route still has to be declared before the
# {nickname} one, which would otherwise match it first.


@router.put("/me/avatar", response_model=AvatarResponse, dependencies=[avatar_write_limit])
async def put_my_avatar(
    request: Request,
    file: UploadFile = File(..., description="JPEG, PNG, WebP, or GIF"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Replace my profile picture with a normalized square rendering of `file`."""
    # Refuse an oversized body up front, when the client says how big it is,
    # rather than after buffering it. _read_capped covers clients that do not.
    declared = request.headers.get("content-length")
    ceiling = settings.avatar_max_upload_bytes + MULTIPART_SLACK
    if declared and declared.isdigit() and int(declared) > ceiling:
        raise _too_large()

    raw = await _read_capped(file)
    try:
        normalized = normalize_avatar(raw)
    except AvatarError as err:
        raise HTTPException(status_code=400, detail=str(err)) from err

    row = db.get(ProfilePicture, current_user.id)
    if row is None:
        row = ProfilePicture(user_id=current_user.id)
        db.add(row)
    row.content_type = AVATAR_CONTENT_TYPE
    row.data = normalized
    db.commit()
    db.refresh(row)
    logger.info(
        "User %s set a profile picture (%d bytes stored)", current_user.id, len(normalized)
    )
    return AvatarResponse(avatar_updated_at=row.updated_at.isoformat() if row.updated_at else None)


@router.delete("/me/avatar", response_model=OkResponse, dependencies=[avatar_write_limit])
def delete_my_avatar(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Remove my profile picture. Idempotent: removing nothing is still fine."""
    row = db.get(ProfilePicture, current_user.id)
    if row is not None:
        db.delete(row)
        db.commit()
    return OkResponse()


@router.get("/me/avatar", response_class=Response)
def get_my_avatar(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """My own profile picture."""
    return _image_response(request, _picture_or_404(db, current_user.id))


@router.get("/{nickname}/avatar", response_class=Response)
def get_user_avatar(
    nickname: str,
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Another user's profile picture, if we are linked.

    Someone you are not linked to is reported as 404 rather than 403, so this
    endpoint cannot be used to test which nicknames exist or which of them have
    uploaded a picture.
    """
    target = (
        db.query(User).filter(func.lower(User.nickname) == nickname.strip().lower()).first()
    )
    if target is None or not _may_see(db, current_user, target):
        raise HTTPException(status_code=404, detail="No profile picture.")
    return _image_response(request, _picture_or_404(db, target.id))
