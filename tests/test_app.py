from copy import deepcopy
from pathlib import Path
import sys

import pytest
from fastapi.testclient import TestClient

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from app import app, activities


@pytest.fixture(autouse=True)
def reset_activities():
    original = deepcopy(activities)
    yield
    activities.clear()
    activities.update(original)


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


def test_activities_endpoint_disables_caching():
    client = TestClient(app)

    response = client.get("/activities")

    assert response.status_code == 200
    assert response.headers.get("cache-control") == "no-store"
