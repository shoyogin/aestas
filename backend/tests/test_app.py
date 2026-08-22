"""Auth surface, served content, and health probes."""
import pytest

from app.phase_content import load_content, panels_for_link


@pytest.fixture
def user(make_user):
    return make_user("alice", starts=["2026-03-01"])


# ----- Auth -----


def test_me_returns_the_current_user(client, login, user):
    login(user)
    body = client.get("/auth/me").json()
    assert body["nickname"] == "alice"
    assert body["timezone"] == "UTC"
    assert body["has_completed_onboarding"] is True


def test_me_requires_a_session(client):
    client.cookies.clear()
    assert client.get("/auth/me").status_code == 401


def test_a_bogus_session_cookie_is_rejected(client):
    client.cookies.set("session", "not-a-real-token")
    assert client.get("/auth/me").status_code == 401


def test_logout_clears_the_session(client, login, user):
    login(user)
    assert client.post("/auth/logout").status_code == 200
    assert client.get("/auth/me").status_code == 401


def test_login_redirects_to_google_with_a_state_cookie(client):
    res = client.get("/auth/google", follow_redirects=False)
    assert res.status_code == 302
    assert res.headers["location"].startswith("https://accounts.google.com/")
    assert "oauth_state" in res.cookies
    # We never use a refresh token, so we must not ask for offline access.
    assert "access_type=offline" not in res.headers["location"]


def test_callback_without_a_matching_state_is_refused(client):
    res = client.get("/auth/callback", params={"code": "x", "state": "forged"},
                     follow_redirects=False)
    assert res.status_code == 302
    assert "error=invalid_state" in res.headers["location"]


def test_callback_surfaces_a_google_error(client):
    res = client.get("/auth/callback", params={"error": "access_denied"},
                     follow_redirects=False)
    assert "error=access_denied" in res.headers["location"]


# ----- Content -----


def test_phase_content_requires_a_session(client):
    client.cookies.clear()
    assert client.get("/content/phases").status_code == 401


def test_phase_content_is_served_to_the_frontend(client, login, user):
    login(user)
    body = client.get("/content/phases").json()
    assert set(body["panels"]) == {"menstrual", "follicular", "ovulation", "luteal"}
    assert body["panel_order"] == ["food", "activity", "mood", "drive"]
    assert body["disclaimer"]


def test_every_phase_has_every_owner_panel():
    content = load_content()
    for phase, panels in content["panels"].items():
        for key in content["panel_order"]:
            assert key in panels, f"{phase} is missing the {key} panel"
            assert panels[key]["title"] and panels[key]["bullets"] and panels[key]["why"]


def test_friend_view_is_a_strict_subset_of_the_partner_view():
    for phase in load_content()["panels"]:
        friend = panels_for_link(phase, "friend")
        partner = panels_for_link(phase, "partner")
        assert "drive" not in friend
        assert "drive" in partner
        assert friend["support"] is None
        assert partner["support"]


def test_no_phase_means_no_panels():
    assert panels_for_link(None, "partner") is None


# ----- Health -----


def test_liveness_touches_no_dependency(client):
    assert client.get("/health").json() == {
        "status": "ok", "database": None, "redis": None
    }


def test_readiness_reports_dependencies(client):
    body = client.get("/health/ready").json()
    assert body == {"status": "ok", "database": "ok", "redis": "ok"}


def test_readiness_fails_when_a_dependency_is_down(client, monkeypatch):
    """A healthcheck that skips this passes while the app cannot serve."""
    monkeypatch.setattr("app.routers.health.redis_ping", lambda: False)
    res = client.get("/health/ready")
    assert res.status_code == 503
    assert res.json()["status"] == "degraded"
