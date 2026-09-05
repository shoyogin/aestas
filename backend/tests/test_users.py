"""Onboarding, profile, search, and daily logs."""
import datetime as dt

import pytest

from app.models import DailyLog


@pytest.fixture
def user(make_user):
    return make_user("alice", cycle_length=None, starts=[])


def _today(tz="UTC"):
    from app.cycle_phase import today_in

    return today_in(tz)


# ----- Onboarding -----


def test_onboarding_records_cycle_length(client, login, user, db):
    login(user)
    assert client.post("/users/onboarding", json={"cycle_length": 30}).status_code == 200
    db.refresh(user)
    assert user.cycle_length == 30


@pytest.mark.parametrize("length", [14, 46, 0, -1])
def test_onboarding_rejects_lengths_outside_the_supported_range(client, login, user, length):
    login(user)
    res = client.post("/users/onboarding", json={"cycle_length": length})
    assert res.status_code == 422


def test_last_cycle_start_is_recorded(client, login, user, db):
    login(user)
    day = _today().isoformat()
    res = client.post("/users/onboarding/last-cycle", json={"last_cycle_start": day})
    assert res.status_code == 200
    assert res.json()["cycle_start_dates"] == [day]


def test_repeating_onboarding_does_not_duplicate_the_start_date(client, login, user):
    """Two submissions of the same day must not look like two cycles."""
    login(user)
    day = _today().isoformat()
    client.post("/users/onboarding/last-cycle", json={"last_cycle_start": day})
    res = client.post("/users/onboarding/last-cycle", json={"last_cycle_start": day})
    assert res.json()["cycle_start_dates"] == [day]


def test_future_cycle_start_is_rejected(client, login, user):
    login(user)
    future = (_today() + dt.timedelta(days=1)).isoformat()
    res = client.post("/users/onboarding/last-cycle", json={"last_cycle_start": future})
    assert res.status_code == 400


def test_prehistoric_cycle_start_is_rejected(client, login, user):
    login(user)
    res = client.post("/users/onboarding/last-cycle", json={"last_cycle_start": "1999-12-31"})
    assert res.status_code == 400


def test_malformed_date_is_rejected(client, login, user):
    login(user)
    res = client.post("/users/onboarding/last-cycle", json={"last_cycle_start": "not-a-date"})
    assert res.status_code == 422


def test_cycle_start_dates_stay_sorted(client, login, user):
    login(user)
    for day in ("2026-03-20", "2026-01-05", "2026-02-10"):
        client.post("/users/onboarding/last-cycle", json={"last_cycle_start": day})
    dates = client.get("/users/cycle-context").json()["cycle_start_dates"]
    assert dates == sorted(dates)


# ----- Profile -----


def test_nickname_is_stored_lowercase(client, login, user):
    login(user)
    assert client.patch("/users/me", json={"nickname": "LuNa_28"}).json()["nickname"] == "luna_28"


@pytest.mark.parametrize("nick", ["ab", "has space", "Uppercase!", "dash-not-allowed", "a" * 25])
def test_invalid_nicknames_are_rejected(client, login, user, nick):
    login(user)
    assert client.patch("/users/me", json={"nickname": nick}).status_code in (400, 422)


def test_nickname_taken_by_someone_else_is_409(client, login, user, make_user):
    make_user("taken")
    login(user)
    assert client.patch("/users/me", json={"nickname": "taken"}).status_code == 409


def test_nickname_collision_is_case_insensitive(client, login, user, make_user):
    make_user("taken")
    login(user)
    assert client.patch("/users/me", json={"nickname": "TAKEN"}).status_code == 409


def test_keeping_your_own_nickname_is_not_a_collision(client, login, user):
    login(user)
    client.patch("/users/me", json={"nickname": "luna_28"})
    assert client.patch("/users/me", json={"nickname": "luna_28"}).status_code == 200


def test_timezone_can_be_set(client, login, user, db):
    login(user)
    res = client.patch("/users/me", json={"timezone": "Europe/Rome"})
    assert res.json()["timezone"] == "Europe/Rome"
    db.refresh(user)
    assert user.timezone == "Europe/Rome"


def test_unknown_timezone_is_rejected(client, login, user):
    login(user)
    assert client.patch("/users/me", json={"timezone": "Mars/Olympus"}).status_code == 400


def test_empty_patch_is_rejected(client, login, user):
    login(user)
    assert client.patch("/users/me", json={}).status_code == 400


# ----- Search -----


def test_search_matches_a_nickname_prefix(client, login, user, make_user):
    make_user("bobby")
    make_user("bobcat")
    make_user("carol")
    login(user)
    hits = client.get("/users/search", params={"nickname": "bob"}).json()
    assert {h["nickname"] for h in hits} == {"bobby", "bobcat"}


def test_search_wildcards_cannot_list_every_user(client, login, user, make_user):
    """A LIKE pattern built from raw input let "%" enumerate the whole table."""
    make_user("bobby")
    make_user("carol")
    login(user)
    assert client.get("/users/search", params={"nickname": "%"}).json() == []
    assert client.get("/users/search", params={"nickname": "_"}).json() == []


def test_search_underscore_still_matches_literally(client, login, user, make_user):
    make_user("luna_28")
    make_user("lunatic")
    login(user)
    hits = client.get("/users/search", params={"nickname": "luna_"}).json()
    assert [h["nickname"] for h in hits] == ["luna_28"]


def test_search_never_returns_email_or_self(client, login, make_user):
    me = make_user("alice")
    make_user("alicia")
    login(me)
    hits = client.get("/users/search", params={"nickname": "ali"}).json()
    assert [h["nickname"] for h in hits] == ["alicia"]
    assert all(set(h) == {"nickname"} for h in hits)


def test_search_is_rate_limited(client, login, user, make_user):
    make_user("bobby")
    login(user)
    statuses = {
        client.get("/users/search", params={"nickname": "bob"}).status_code
        for _ in range(40)
    }
    assert 429 in statuses


# ----- Daily logs -----


def test_logging_a_period_start_sets_awaiting_end(client, login, user, db):
    login(user)
    day = _today().isoformat()
    res = client.post(
        "/users/daily-logs",
        json={"date": day, "is_period": True, "period_event": "start"},
    )
    assert res.status_code == 200
    assert res.json()["awaiting_period_end"] is True
    assert res.json()["cycle_start_dates"] == [day]


def test_logging_a_period_end_clears_awaiting_end(client, login, user):
    login(user)
    start = (_today() - dt.timedelta(days=4)).isoformat()
    end = _today().isoformat()
    client.post(
        "/users/daily-logs",
        json={"date": start, "is_period": True, "period_event": "start"},
    )
    res = client.post(
        "/users/daily-logs",
        json={"date": end, "is_period": True, "period_event": "end"},
    )
    assert res.json()["awaiting_period_end"] is False
    assert res.json()["cycle_end_dates"] == [end]


def test_tapping_period_started_twice_records_one_cycle(client, login, user):
    login(user)
    day = _today().isoformat()
    body = {"date": day, "is_period": True, "period_event": "start"}
    client.post("/users/daily-logs", json=body)
    res = client.post("/users/daily-logs", json=body)
    assert res.json()["cycle_start_dates"] == [day]


def test_upserting_the_same_day_updates_rather_than_duplicating(client, login, user, db):
    login(user)
    day = _today().isoformat()
    client.post("/users/daily-logs", json={"date": day, "flow": "light"})
    res = client.post("/users/daily-logs", json={"date": day, "flow": "heavy"})
    assert res.json()["flow"] == "heavy"
    assert db.query(DailyLog).filter(DailyLog.user_id == user.id).count() == 1


def test_flow_can_be_cleared(client, login, user):
    login(user)
    day = _today().isoformat()
    client.post("/users/daily-logs", json={"date": day, "flow": "light"})
    assert client.post("/users/daily-logs", json={"date": day, "flow": None}).json()["flow"] is None


def test_omitting_flow_leaves_it_untouched(client, login, user):
    """Only send what changed: a period tap must not wipe the flow."""
    login(user)
    day = _today().isoformat()
    client.post("/users/daily-logs", json={"date": day, "flow": "normal"})
    res = client.post("/users/daily-logs", json={"date": day, "is_period": True})
    assert res.json()["flow"] == "normal"


def test_invalid_flow_is_rejected(client, login, user):
    login(user)
    res = client.post(
        "/users/daily-logs", json={"date": _today().isoformat(), "flow": "torrential"}
    )
    assert res.status_code == 400


def test_invalid_period_event_is_rejected(client, login, user):
    login(user)
    res = client.post(
        "/users/daily-logs", json={"date": _today().isoformat(), "period_event": "middle"}
    )
    assert res.status_code == 400


def test_daily_logs_are_returned_for_a_range(client, login, user):
    login(user)
    base = _today() - dt.timedelta(days=5)
    for offset in range(3):
        client.post(
            "/users/daily-logs",
            json={"date": (base + dt.timedelta(days=offset)).isoformat(), "flow": "light"},
        )
    rows = client.get(
        "/users/daily-logs",
        params={"from": base.isoformat(), "to": (base + dt.timedelta(days=1)).isoformat()},
    ).json()
    assert [r["date"] for r in rows] == [
        base.isoformat(), (base + dt.timedelta(days=1)).isoformat()
    ]


def test_reversed_range_is_rejected(client, login, user):
    login(user)
    res = client.get("/users/daily-logs", params={"from": "2026-03-10", "to": "2026-03-01"})
    assert res.status_code == 400


def test_daily_logs_are_scoped_to_the_current_user(client, login, user, make_user):
    other = make_user("bob")
    login(other)
    client.post("/users/daily-logs", json={"date": _today().isoformat(), "flow": "heavy"})
    login(user)
    rows = client.get(
        "/users/daily-logs",
        params={"from": _today().isoformat(), "to": _today().isoformat()},
    ).json()
    assert rows == []


def test_user_endpoints_require_authentication(client, user):
    client.cookies.clear()
    assert client.get("/users/cycle-context").status_code == 401
    assert client.patch("/users/me", json={"nickname": "luna_28"}).status_code == 401
