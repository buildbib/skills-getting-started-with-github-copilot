from copy import deepcopy
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


def test_root_redirects_to_static_index():
    client = TestClient(app)

    response = client.get("/", follow_redirects=False)

    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/static/index.html"


def test_activities_endpoint_disables_caching():
    client = TestClient(app)

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"


def test_signup_adds_participant_to_activity():
    client = TestClient(app)

    response = client.post("/activities/Chess Club/signup?email=newstudent@mergington.edu")

    assert response.status_code == 200
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]
    assert response.json()["message"] == "Signed up newstudent@mergington.edu for Chess Club"


def test_signup_rejects_duplicate_participant():
    client = TestClient(app)

    response = client.post("/activities/Chess Club/signup?email=michael@mergington.edu")

    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_signup_returns_not_found_for_unknown_activity():
    client = TestClient(app)

    response = client.post("/activities/Unknown Activity/signup?email=newstudent@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_participant_removes_their_registration():
    client = TestClient(app)
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    response = client.post(f"/activities/{activity_name}/unregister?email={email}")

    assert response.status_code == 200
    assert email not in activities[activity_name]["participants"]
    assert response.json()["message"] == f"Removed {email} from {activity_name}"


def test_unregister_unknown_participant_returns_not_found():
    client = TestClient(app)

    response = client.post("/activities/Chess Club/unregister?email=ghost@mergington.edu")

    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found"
