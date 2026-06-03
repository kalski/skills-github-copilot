import copy

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)


@pytest.fixture(autouse=True)
def restore_activities():
    """Reset the in-memory activities data after each test."""
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_activity_mapping():
    # Arrange
    expected_activity = "Chess Club"

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    body = response.json()
    assert expected_activity in body
    assert body[expected_activity]["description"] == "Learn strategies and compete in chess tournaments"


def test_signup_for_activity_adds_participant():
    # Arrange
    activity_name = "Chess Club"
    new_email = "test.student@mergington.edu"
    assert new_email not in activities[activity_name]["participants"]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": new_email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {new_email} for {activity_name}"}
    assert new_email in activities[activity_name]["participants"]


def test_signup_for_activity_rejects_duplicate_signup():
    # Arrange
    activity_name = "Chess Club"
    duplicate_email = activities[activity_name]["participants"][0]

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": duplicate_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"


def test_signup_for_missing_activity_returns_404():
    # Arrange
    activity_name = "Nonexistent Club"
    email = "new.student@mergington.edu"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup",
        params={"email": email}
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_from_activity_removes_participant():
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = activities[activity_name]["participants"][0]
    assert email_to_remove in activities[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": email_to_remove}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Removed {email_to_remove} from {activity_name}"}
    assert email_to_remove not in activities[activity_name]["participants"]


def test_unregister_from_activity_rejects_unregistered_student():
    # Arrange
    activity_name = "Chess Club"
    unregistered_email = "not.registered@mergington.edu"
    assert unregistered_email not in activities[activity_name]["participants"]

    # Act
    response = client.delete(
        f"/activities/{activity_name}/unregister",
        params={"email": unregistered_email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_root_redirects_to_static_index_html():
    # Arrange

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code in {307, 308}
    assert response.headers["location"] == "/static/index.html"
