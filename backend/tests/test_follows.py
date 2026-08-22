"""Follow lifecycle: the Instagram model, and the access-control rules around it."""
import pytest


@pytest.fixture
def alice(make_user):
    return make_user("alice", starts=["2026-03-01"])


@pytest.fixture
def bob(make_user):
    return make_user("bob", starts=["2026-03-01"])


def _request(client, nickname="bob", link_type="friend"):
    return client.post("/follows", json={"nickname": nickname, "link_type": link_type})


# ----- Sending -----


def test_request_creates_a_pending_follow(client, login, alice, bob):
    login(alice)
    res = _request(client)
    assert res.status_code == 200
    body = res.json()
    assert body["status"] == "pending"
    assert body["nickname"] == "bob"
    assert body["direction"] == "outgoing"


def test_cannot_follow_yourself(client, login, alice):
    login(alice)
    assert _request(client, "alice").status_code == 400


def test_unknown_nickname_is_404(client, login, alice):
    login(alice)
    assert _request(client, "nobody").status_code == 404


def test_invalid_link_type_is_rejected(client, login, alice, bob):
    login(alice)
    assert _request(client, "bob", "stalker").status_code == 400


def test_duplicate_request_while_pending_is_409(client, login, alice, bob):
    login(alice)
    _request(client)
    assert _request(client).status_code == 409


def test_requesting_someone_you_already_follow_is_409(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")
    login(alice)
    assert _request(client).status_code == 409


def test_nickname_lookup_is_case_insensitive(client, login, alice, bob):
    login(alice)
    assert _request(client, "BoB").status_code == 200


# ----- Withdraw and re-request (the only moves before acceptance) -----


def test_requester_can_withdraw_a_pending_request(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    assert client.delete(f"/follows/{follow_id}").status_code == 200

    login(bob)
    assert client.get("/follows/inbox").json() == []


def test_withdrawn_request_can_be_sent_again(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    client.delete(f"/follows/{follow_id}")

    again = _request(client)
    assert again.status_code == 200
    assert again.json()["status"] == "pending"
    # The same row is reused, so the unique constraint is never violated.
    assert again.json()["id"] == follow_id


def test_refused_request_can_be_sent_again(client, login, alice, bob):
    """Instagram semantics: a decline does not permanently bar the requester."""
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/refuse")

    login(alice)
    assert _request(client).status_code == 200


def test_target_cannot_withdraw_a_request_sent_to_them(client, login, alice, bob):
    """The target refuses; only the requester withdraws."""
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    assert client.delete(f"/follows/{follow_id}").status_code == 409


def test_outgoing_requests_are_listed_so_they_can_be_cancelled(client, login, alice, bob):
    login(alice)
    _request(client)
    rows = client.get("/follows/requests").json()
    assert [(r["nickname"], r["status"]) for r in rows] == [("bob", "pending")]


def test_pending_requests_do_not_expire(client, login, alice, bob, db):
    """The old 14-day inbox cutoff hid requests while still blocking new ones."""
    import datetime as dt

    from app.models import FollowRequest

    login(alice)
    follow_id = _request(client).json()["id"]
    row = db.query(FollowRequest).filter(FollowRequest.id == follow_id).one()
    row.created_at = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=365)
    db.commit()

    login(bob)
    assert len(client.get("/follows/inbox").json()) == 1


# ----- Accepting and refusing -----


def test_accept_makes_the_phase_visible(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    assert client.post(f"/follows/{follow_id}/accept").status_code == 200

    login(alice)
    rows = client.get("/follows").json()
    assert len(rows) == 1
    assert rows[0]["phase"] is not None
    assert rows[0]["cycle_day"] is not None


def test_only_the_target_can_accept(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    assert client.post(f"/follows/{follow_id}/accept").status_code == 403


def test_cannot_accept_twice(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")
    assert client.post(f"/follows/{follow_id}/accept").status_code == 409


def test_only_one_accepted_partner_at_a_time(client, login, make_user, bob):
    first = make_user("carol")
    second = make_user("dave")

    login(first)
    a = _request(client, "bob", "partner").json()["id"]
    login(second)
    b = _request(client, "bob", "partner").json()["id"]

    login(bob)
    assert client.post(f"/follows/{a}/accept").status_code == 200
    assert client.post(f"/follows/{b}/accept").status_code == 409


def test_a_second_friend_follow_is_fine(client, login, make_user, bob):
    first = make_user("carol")
    second = make_user("dave")
    login(first)
    a = _request(client, "bob", "friend").json()["id"]
    login(second)
    b = _request(client, "bob", "friend").json()["id"]
    login(bob)
    assert client.post(f"/follows/{a}/accept").status_code == 200
    assert client.post(f"/follows/{b}/accept").status_code == 200


# ----- Revoking access already granted -----


def test_followers_are_listed_so_access_can_be_taken_back(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")

    followers = client.get("/follows/followers").json()
    assert [(f["nickname"], f["direction"]) for f in followers] == [("alice", "incoming")]


def test_target_can_remove_a_follower(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")
    assert client.delete(f"/follows/{follow_id}").status_code == 200

    login(alice)
    assert client.get("/follows").json() == []
    assert client.get(f"/follows/{follow_id}/cycle").status_code == 404


def test_requester_can_unfollow(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")
    login(alice)
    assert client.delete(f"/follows/{follow_id}").status_code == 200
    assert client.get("/follows").json() == []


def test_a_stranger_cannot_touch_someone_elses_follow(client, login, alice, bob, make_user):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(make_user("mallory"))
    assert client.delete(f"/follows/{follow_id}").status_code == 403
    assert client.post(f"/follows/{follow_id}/accept").status_code == 403
    assert client.get(f"/follows/{follow_id}/cycle").status_code == 403


# ----- The shared view -----


def test_friend_view_omits_the_drive_panel(client, login, alice, bob):
    login(alice)
    follow_id = _request(client, "bob", "friend").json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")

    login(alice)
    panels = client.get(f"/follows/{follow_id}/cycle").json()["panels"]
    assert "drive" not in panels
    assert panels["support"] is None


def test_partner_view_includes_drive_and_support(client, login, alice, bob):
    login(alice)
    follow_id = _request(client, "bob", "partner").json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")

    login(alice)
    panels = client.get(f"/follows/{follow_id}/cycle").json()["panels"]
    assert "drive" in panels
    assert panels["support"]


def test_shared_view_never_leaks_dates_or_email(client, login, alice, bob):
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")

    login(alice)
    body = client.get(f"/follows/{follow_id}/cycle").json()
    assert set(body) == {
        "nickname", "link_type", "phase", "cycle_day", "phase_label",
        "panels", "disclaimer",
    }
    assert "2026-03-01" not in str(body)
    assert "bob@example.com" not in str(body)


def test_the_target_cannot_read_their_own_shared_view(client, login, alice, bob):
    """Only the follower reads this endpoint; it is not a self-service view."""
    login(alice)
    follow_id = _request(client).json()["id"]
    login(bob)
    client.post(f"/follows/{follow_id}/accept")
    assert client.get(f"/follows/{follow_id}/cycle").status_code == 403


def test_following_someone_with_no_cycle_data_reports_no_phase(client, login, alice, make_user):
    blank = make_user("erin", cycle_length=None)
    login(alice)
    follow_id = _request(client, "erin").json()["id"]
    login(blank)
    client.post(f"/follows/{follow_id}/accept")

    login(alice)
    assert client.get("/follows").json()[0]["phase"] is None


def test_follow_endpoints_require_authentication(client, alice):
    client.cookies.clear()
    assert client.get("/follows").status_code == 401
    assert client.get("/follows/inbox").status_code == 401
    assert _request(client).status_code == 401
