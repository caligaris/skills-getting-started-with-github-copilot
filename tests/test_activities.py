import copy
import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset the in-memory activities database before each test."""
    original = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


@pytest.fixture
def client():
    return TestClient(app)


# ---------------------------------------------------------------------------
# GET /
# ---------------------------------------------------------------------------


class TestRootRedirect:
    def test_redirects_to_static_index(self, client):
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert "/static/index.html" in response.headers["location"]


# ---------------------------------------------------------------------------
# GET /activities
# ---------------------------------------------------------------------------


class TestGetActivities:
    def test_returns_all_activities(self, client):
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 9

    def test_activity_has_expected_keys(self, client):
        response = client.get("/activities")
        data = response.json()
        for name, info in data.items():
            assert "description" in info
            assert "schedule" in info
            assert "max_participants" in info
            assert "participants" in info

    def test_known_activity_present(self, client):
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data


# ---------------------------------------------------------------------------
# POST /activities/{activity_name}/signup
# ---------------------------------------------------------------------------


class TestSignup:
    def test_successful_signup(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "newstudent@mergington.edu"},
        )
        assert response.status_code == 200
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_duplicate_signup_returns_400(self, client):
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_nonexistent_activity_returns_404(self, client):
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_missing_email_returns_422(self, client):
        response = client.post("/activities/Chess Club/signup")
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# DELETE /activities/{activity_name}/signup
# ---------------------------------------------------------------------------


class TestUnregister:
    def test_successful_unregister(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "michael@mergington.edu"},
        )
        assert response.status_code == 200
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_not_signed_up_returns_400(self, client):
        response = client.delete(
            "/activities/Chess Club/signup",
            params={"email": "unknown@mergington.edu"},
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()

    def test_nonexistent_activity_returns_404(self, client):
        response = client.delete(
            "/activities/Nonexistent Club/signup",
            params={"email": "student@mergington.edu"},
        )
        assert response.status_code == 404

    def test_missing_email_returns_422(self, client):
        response = client.delete("/activities/Chess Club/signup")
        assert response.status_code == 422
