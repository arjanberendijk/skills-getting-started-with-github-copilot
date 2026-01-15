import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Add src directory to path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from app import app

client = TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    from app import activities
    
    # Store original state
    original = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Join the team and compete in local tournaments",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Soccer Club": {
            "description": "Practice soccer skills and play matches",
            "schedule": "Mondays and Wednesdays, 3:00 PM - 5:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Art Club": {
            "description": "Explore various art techniques and create projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Drama Club": {
            "description": "Participate in theater productions and improve acting skills",
            "schedule": "Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 20,
            "participants": []
        },
        "Debate Team": {
            "description": "Engage in debates and improve public speaking skills",
            "schedule": "Fridays, 3:00 PM - 5:00 PM",
            "max_participants": 12,
            "participants": []
        },
        "Math Club": {
            "description": "Solve challenging math problems and compete in contests",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 10,
            "participants": []
        }
    }
    
    # Clear and restore
    activities.clear()
    activities.update(original)
    
    yield
    
    # Cleanup
    activities.clear()
    activities.update(original)


class TestGetActivities:
    def test_get_activities(self, reset_activities):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, dict)
        assert "Chess Club" in data
        assert "Programming Class" in data
        
    def test_activities_structure(self, reset_activities):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert "description" in activity
        assert "schedule" in activity
        assert "max_participants" in activity
        assert "participants" in activity
        assert isinstance(activity["participants"], list)


class TestSignup:
    def test_signup_success(self, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup?email=newstudent@mergington.edu",
            json={}
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        
        # Verify student was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "newstudent@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_signup_activity_not_found(self, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=student@mergington.edu",
            json={}
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_signup_already_registered(self, reset_activities):
        """Test signup when student is already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu",
            json={}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]
    
    def test_signup_multiple_students(self, reset_activities):
        """Test multiple students signing up for an activity"""
        response1 = client.post(
            "/activities/Basketball Team/signup?email=student1@mergington.edu",
            json={}
        )
        response2 = client.post(
            "/activities/Basketball Team/signup?email=student2@mergington.edu",
            json={}
        )
        
        assert response1.status_code == 200
        assert response2.status_code == 200
        
        activities_response = client.get("/activities")
        participants = activities_response.json()["Basketball Team"]["participants"]
        assert "student1@mergington.edu" in participants
        assert "student2@mergington.edu" in participants


class TestUnregister:
    def test_unregister_success(self, reset_activities):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
        
        # Verify student was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "michael@mergington.edu" not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_activity_not_found(self, reset_activities):
        """Test unregister from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]
    
    def test_unregister_not_registered(self, reset_activities):
        """Test unregister when student is not registered"""
        response = client.delete(
            "/activities/Chess Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"]
    
    def test_unregister_all_participants(self, reset_activities):
        """Test unregistering all participants from an activity"""
        # First, unregister all existing participants
        activity_data = client.get("/activities").json()
        participants = activity_data["Chess Club"]["participants"].copy()
        
        for participant in participants:
            response = client.delete(
                f"/activities/Chess Club/unregister?email={participant}"
            )
            assert response.status_code == 200
        
        # Verify all participants are removed
        activities_response = client.get("/activities")
        assert len(activities_response.json()["Chess Club"]["participants"]) == 0


class TestRoot:
    def test_root_redirect(self):
        """Test that root redirects to static/index.html"""
        response = client.get("/", follow_redirects=True)
        assert response.status_code == 200
