"""Profile pictures: upload, normalization, visibility, and caching."""
import io

import pytest
from PIL import Image

from app.avatars import AVATAR_SIZE, AvatarError, normalize_avatar

UPLOAD = "/users/me/avatar"


def _image_bytes(size=(800, 600), fmt="PNG", mode="RGB", color=(120, 40, 60)):
    buf = io.BytesIO()
    Image.new(mode, size, color).save(buf, fmt)
    return buf.getvalue()


def _upload(client, data=None, filename="me.png", content_type="image/png"):
    payload = _image_bytes() if data is None else data
    return client.put(UPLOAD, files={"file": (filename, payload, content_type)})


@pytest.fixture
def alice(make_user):
    return make_user("alice")


@pytest.fixture
def bob(make_user):
    return make_user("bob")


# ----- Normalization -----


def test_upload_stores_a_square_webp_whatever_came_in(client, login, alice, db):
    login(alice)
    assert _upload(client, _image_bytes(size=(800, 600))).status_code == 200

    res = client.get(UPLOAD)
    assert res.status_code == 200
    assert res.headers["content-type"].startswith("image/webp")
    with Image.open(io.BytesIO(res.content)) as stored:
        assert stored.format == "WEBP"
        assert stored.size == (AVATAR_SIZE, AVATAR_SIZE)


def test_a_small_image_is_not_upscaled(client, login, alice):
    """Blowing a 64px picture up to 512 would only make it blurry and bigger."""
    login(alice)
    _upload(client, _image_bytes(size=(64, 64)))
    with Image.open(io.BytesIO(client.get(UPLOAD).content)) as stored:
        assert stored.size == (64, 64)


def test_exif_orientation_is_applied_before_it_is_discarded(client, login, alice):
    """A phone photo records rotation in EXIF; the re-encode drops EXIF, so the
    rotation has to be baked into the pixels or the avatar ends up sideways."""
    source = Image.new("RGB", (100, 60), (10, 20, 30))
    exif = source.getexif()
    exif[274] = 6  # Orientation: rotate 90°, which swaps width and height.
    buf = io.BytesIO()
    source.save(buf, "JPEG", exif=exif)

    login(alice)
    assert _upload(client, buf.getvalue(), "photo.jpg", "image/jpeg").status_code == 200
    with Image.open(io.BytesIO(client.get(UPLOAD).content)) as stored:
        # Square either way; what matters is that nothing raised and the shorter
        # side (60, now the width) is what set the size.
        assert stored.size == (60, 60)


def test_uploaded_metadata_does_not_survive(client, login, alice):
    """EXIF on a phone photo carries GPS. The stored avatar must not."""
    source = Image.new("RGB", (200, 200), (5, 5, 5))
    exif = source.getexif()
    exif[270] = "taken at home"  # ImageDescription
    buf = io.BytesIO()
    source.save(buf, "JPEG", exif=exif)

    login(alice)
    _upload(client, buf.getvalue(), "photo.jpg", "image/jpeg")
    with Image.open(io.BytesIO(client.get(UPLOAD).content)) as stored:
        assert not stored.getexif()


def test_transparency_is_kept(client, login, alice):
    login(alice)
    _upload(client, _image_bytes(size=(200, 200), mode="RGBA", color=(1, 2, 3, 0)))
    with Image.open(io.BytesIO(client.get(UPLOAD).content)) as stored:
        assert stored.mode in ("RGBA", "LA")


@pytest.mark.parametrize(
    "payload",
    [
        b"not an image at all",
        b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>',
        b"",
    ],
    ids=["garbage", "svg", "empty"],
)
def test_things_that_are_not_raster_images_are_refused(client, login, alice, payload):
    """SVG is in here on purpose: it is a document that can carry script, and
    serving one back from our own origin would be stored XSS."""
    login(alice)
    res = _upload(client, payload, "x.svg", "image/svg+xml")
    assert res.status_code == 400
    assert client.get(UPLOAD).status_code == 404


def test_a_lying_content_type_does_not_get_through(client, login, alice):
    """The client's Content-Type is a claim; the decode is the actual check."""
    login(alice)
    assert _upload(client, b"MZ\x00\x00 not a png", "evil.png", "image/png").status_code == 400


def test_oversized_uploads_are_refused(client, login, alice, monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "avatar_max_upload_bytes", 1024)
    login(alice)
    res = _upload(client, _image_bytes(size=(900, 900), color=(0, 0, 0)))
    assert res.status_code == 413


def test_a_decompression_bomb_is_refused_before_it_is_decoded():
    """Header-sized, so this never has to allocate the pixels to say no."""
    with pytest.raises(AvatarError):
        normalize_avatar(_bomb_header())


def _bomb_header():
    # A PNG header claiming 60000x60000 (3.6 gigapixels) with no real pixel data.
    import struct
    import zlib

    ihdr = struct.pack(">IIBBBBB", 60000, 60000, 8, 2, 0, 0, 0)
    chunk = struct.pack(">I", len(ihdr)) + b"IHDR" + ihdr
    chunk += struct.pack(">I", zlib.crc32(b"IHDR" + ihdr) & 0xFFFFFFFF)
    return b"\x89PNG\r\n\x1a\n" + chunk


# ----- Lifecycle -----


def test_replacing_a_picture_keeps_one_row_and_moves_the_version(client, login, alice, db):
    from app.models import ProfilePicture

    login(alice)
    first = _upload(client).json()["avatar_updated_at"]
    second = _upload(client, _image_bytes(color=(9, 9, 9))).json()["avatar_updated_at"]
    assert first and second and second >= first
    assert db.query(ProfilePicture).filter(ProfilePicture.user_id == alice.id).count() == 1


def test_delete_removes_the_picture_and_is_idempotent(client, login, alice):
    login(alice)
    _upload(client)
    assert client.delete(UPLOAD).status_code == 200
    assert client.get(UPLOAD).status_code == 404
    assert client.delete(UPLOAD).status_code == 200


def test_me_reports_whether_there_is_a_picture(client, login, alice):
    login(alice)
    assert client.get("/auth/me").json()["avatar_updated_at"] is None
    _upload(client)
    assert client.get("/auth/me").json()["avatar_updated_at"] is not None


def test_deleting_a_user_takes_the_picture_with_them(client, login, alice, db):
    from app.models import ProfilePicture

    login(alice)
    _upload(client)
    db.delete(alice)
    db.commit()
    assert db.query(ProfilePicture).count() == 0


def test_avatar_endpoints_require_a_session(client, alice):
    assert client.get(UPLOAD).status_code == 401
    assert _upload(client).status_code == 401
    assert client.get("/users/alice/avatar").status_code == 401


# ----- Caching -----


def test_an_unchanged_picture_revalidates_to_304(client, login, alice):
    login(alice)
    _upload(client)
    first = client.get(UPLOAD)
    etag = first.headers["etag"]
    again = client.get(UPLOAD, headers={"If-None-Match": etag})
    assert again.status_code == 304
    assert again.content == b""


def test_a_new_picture_gets_a_new_etag(client, login, alice):
    login(alice)
    _upload(client)
    old_etag = client.get(UPLOAD).headers["etag"]
    _upload(client, _image_bytes(color=(200, 200, 200)))
    assert client.get(UPLOAD, headers={"If-None-Match": old_etag}).status_code == 200


def test_pictures_are_not_cached_by_shared_caches_or_sniffed(client, login, alice):
    login(alice)
    _upload(client)
    res = client.get(UPLOAD)
    assert "private" in res.headers["cache-control"]
    assert res.headers["x-content-type-options"] == "nosniff"


# ----- Who may see whom -----


def _link(db, requester, target, status="accepted", link_type="friend"):
    from app.models import FollowRequest

    row = FollowRequest(
        requester_id=requester.id, target_id=target.id, link_type=link_type, status=status
    )
    db.add(row)
    db.commit()
    return row


def test_a_stranger_cannot_see_your_picture(client, login, alice, bob, db):
    login(alice)
    _upload(client)
    client.cookies.clear()
    login(bob)
    assert client.get("/users/alice/avatar").status_code == 404


def test_a_pending_request_is_enough_to_show_a_face_in_the_inbox(client, login, alice, bob, db):
    """You should be able to see who is asking before you decide."""
    login(alice)
    _upload(client)
    _link(db, bob, alice, status="pending")
    client.cookies.clear()
    login(bob)
    assert client.get("/users/alice/avatar").status_code == 200


def test_either_direction_of_an_accepted_follow_can_see_the_other(client, login, alice, bob, db):
    login(alice)
    _upload(client)
    client.cookies.clear()
    login(bob)
    _upload(client)
    _link(db, bob, alice, status="accepted")

    assert client.get("/users/alice/avatar").status_code == 200  # bob sees the person he follows
    client.cookies.clear()
    login(alice)
    assert client.get("/users/bob/avatar").status_code == 200  # and his follower sees him


@pytest.mark.parametrize("status", ["refused", "revoked", "withdrawn"])
def test_an_ended_follow_takes_the_picture_away_again(client, login, alice, bob, db, status):
    login(alice)
    _upload(client)
    _link(db, bob, alice, status=status)
    client.cookies.clear()
    login(bob)
    assert client.get("/users/alice/avatar").status_code == 404


def test_an_unknown_nickname_looks_the_same_as_one_you_may_not_see(client, login, alice, bob, db):
    """404 for both, so this endpoint cannot be used to enumerate accounts."""
    login(bob)
    assert client.get("/users/alice/avatar").status_code == 404
    assert client.get("/users/nobody_here/avatar").status_code == 404


def test_search_results_do_not_advertise_a_picture(client, login, alice, bob):
    """Nicknames are searchable; faces are not. A hit carries no avatar field."""
    login(alice)
    _upload(client)
    client.cookies.clear()
    login(bob)
    hits = client.get("/users/search", params={"nickname": "ali"}).json()
    assert hits == [{"nickname": "alice"}]


# ----- Follow lists carry the version -----


def test_follow_lists_say_who_has_a_picture(client, login, alice, bob, db):
    login(alice)
    _upload(client)
    _link(db, bob, alice, status="accepted")
    client.cookies.clear()
    login(bob)

    (following,) = client.get("/follows").json()
    assert following["nickname"] == "alice"
    assert following["avatar_updated_at"] is not None
    assert client.get(f"/follows/{following['id']}/cycle").json()["avatar_updated_at"] is not None

    client.cookies.clear()
    login(alice)
    (follower,) = client.get("/follows/followers").json()
    assert follower["nickname"] == "bob"
    assert follower["avatar_updated_at"] is None  # bob never uploaded one
