"""
Comprehensive tests for the FastAPI activities application.

Tests cover all endpoints (GET /activities, POST /signup, DELETE /unregister)
with happy paths, error cases, edge cases, and validation scenarios.
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Fixture providing a TestClient for the FastAPI app."""
    return TestClient(app)


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        # Verify response is a dict with activity names as keys
        assert isinstance(data, dict)
        assert len(data) > 0
        
        # Check that expected activities exist
        expected_activities = ["Chess Club", "Programming Class", "Gym Class"]
        for activity in expected_activities:
            assert activity in data
    
    def test_get_activities_response_structure(self, client):
        """Test that each activity has the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        # Verify each activity has required fields
        for activity_name, details in data.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            
            # Verify field types
            assert isinstance(details["description"], str)
            assert isinstance(details["schedule"], str)
            assert isinstance(details["max_participants"], int)
            assert isinstance(details["participants"], list)
    
    def test_get_activities_participants_populated(self, client):
        """Test that activities have participants in the list"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data.get("Chess Club")
        assert chess_club is not None
        assert len(chess_club["participants"]) > 0
        assert "michael@mergington.edu" in chess_club["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        email = "newstudent@mergington.edu"
        activity = "Chess Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert email in data["message"]
        assert activity in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds the participant to the activity"""
        email = "newtestuser@mergington.edu"
        activity = "Tennis Club"
        
        # Get initial participants count
        activities_before = client.get("/activities").json()
        initial_count = len(activities_before[activity]["participants"])
        
        # Sign up
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_after = client.get("/activities").json()
        assert email in activities_after[activity]["participants"]
        assert len(activities_after[activity]["participants"]) == initial_count + 1
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_duplicate_signup_returns_error(self, client):
        """Test that signing up twice returns 400 error"""
        email = "duplicate@mergington.edu"
        activity = "Drama Club"
        
        # First signup - should succeed
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup - should fail with 400
        response2 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        data = response2.json()
        assert "already signed up" in data["detail"]
    
    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email (URL encoded)"""
        email = "student+test@mergington.edu"
        activity = "Science Club"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200
        
        # Verify participant was added with special characters intact
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]
    
    def test_signup_with_special_characters_in_activity_name(self, client):
        """Test signup with special characters in activity name (URL encoded)"""
        # Create a test with an existing activity
        email = "testuser@mergington.edu"
        activity = "Art Studio"
        
        response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_successful_unregister(self, client):
        """Test successful unregistration from an activity"""
        email = "testunregister@mergington.edu"
        activity = "Debate Team"
        
        # First, sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Then, unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        data = unregister_response.json()
        assert "Unregistered" in data["message"]
        assert email in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes the participant"""
        email = "removeme@mergington.edu"
        activity = "Basketball Team"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify participant is in the list
        activities_before = client.get("/activities").json()
        assert email in activities_before[activity]["participants"]
        
        # Unregister
        response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was removed
        activities_after = client.get("/activities").json()
        assert email not in activities_after[activity]["participants"]
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister for non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonexistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        
        assert response.status_code == 404
        data = response.json()
        assert "Activity not found" in data["detail"]
    
    def test_unregister_participant_not_registered(self, client):
        """Test unregister for participant not in activity returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"]
    
    def test_unregister_then_signup_again(self, client):
        """Test that a student can unregister and then sign up again"""
        email = "reregister@mergington.edu"
        activity = "Art Studio"
        
        # Sign up
        response1 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Unregister
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 200
        
        # Sign up again - should succeed since they're no longer registered
        response3 = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert response3.status_code == 200
        
        # Verify they're in the list
        activities = client.get("/activities").json()
        assert email in activities[activity]["participants"]


class TestEdgeCasesAndValidation:
    """Tests for edge cases and validation scenarios"""
    
    def test_multiple_participants_signup_same_activity(self, client):
        """Test that multiple different participants can sign up for same activity"""
        activity = "Programming Class"
        emails = [
            "user1@mergington.edu",
            "user2@mergington.edu",
            "user3@mergington.edu"
        ]
        
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all are in the activity
        activities = client.get("/activities").json()
        for email in emails:
            assert email in activities[activity]["participants"]
    
    def test_participant_signup_different_activities(self, client):
        """Test that same participant can sign up for different activities"""
        email = "multiactivity@mergington.edu"
        activities = ["Chess Club", "Gym Class", "Debate Team"]
        
        for activity in activities:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify participant is in all activities
        all_activities = client.get("/activities").json()
        for activity in activities:
            assert email in all_activities[activity]["participants"]
    
    def test_unregister_multiple_times_same_participant(self, client):
        """Test that unregistering same participant twice returns error"""
        email = "doubleunregister@mergington.edu"
        activity = "Science Club"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # First unregister - should succeed
        response1 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second unregister - should fail
        response2 = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "not registered" in response2.json()["detail"]
    
    def test_state_persistence_across_requests(self, client):
        """Test that state changes persist across multiple requests"""
        email = "persistence@mergington.edu"
        activity = "Tennis Club"
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Make multiple GET requests
        for _ in range(3):
            activities = client.get("/activities").json()
            assert email in activities[activity]["participants"]
