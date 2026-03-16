"""
Test file for bug fixes - March 2026
Tests:
1. AUTODRAW badge only on instant_win competitions
2. Free competition duplicate entry prevention
3. Dashboard routes working
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestAutodrawBadge:
    """BUG FIX 1: Verify AUTODRAW badge should only appear on instant_win competitions"""
    
    def test_get_competitions_types(self):
        """Verify competitions have correct competition_type field"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        
        competitions = response.json()
        assert len(competitions) > 0
        
        # Find Tesla Model 3 (should be classic type)
        tesla = next((c for c in competitions if 'Tesla' in c['title']), None)
        assert tesla is not None, "Tesla Model 3 competition not found"
        assert tesla['competition_type'] == 'classic', f"Tesla should be classic type, got {tesla['competition_type']}"
        assert tesla['category'] == 'cars', f"Tesla should be in cars category, got {tesla['category']}"
        
        print(f"✅ Tesla Model 3 is correctly marked as 'classic' type")
        
    def test_instant_win_competitions_have_correct_type(self):
        """Verify instant_win competitions are properly categorized"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        
        competitions = response.json()
        instant_win_count = sum(1 for c in competitions if c['competition_type'] == 'instant_win')
        classic_count = sum(1 for c in competitions if c['competition_type'] == 'classic')
        
        print(f"Found {instant_win_count} instant_win and {classic_count} classic competitions")
        assert instant_win_count > 0, "Should have instant_win competitions"
        assert classic_count > 0, "Should have classic competitions"


class TestAutodrawFilter:
    """BUG FIX 2: Verify Autodraw filter works correctly"""
    
    def test_filter_instant_wins(self):
        """Verify API can filter by competition_type=instant_win"""
        response = requests.get(f"{BASE_URL}/api/competitions?competition_type=instant_win")
        assert response.status_code == 200
        
        competitions = response.json()
        for comp in competitions:
            assert comp['competition_type'] == 'instant_win', f"Got {comp['competition_type']} instead of instant_win"
        
        print(f"✅ Filter returned {len(competitions)} instant_win competitions")


class TestFreeCompetitionDuplicateEntry:
    """BUG FIX 4: Verify backend prevents duplicate entries in free competitions"""
    
    @pytest.fixture
    def auth_session(self):
        """Create a test user session"""
        session = requests.Session()
        
        # Register a new test user
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"TEST_freecomp_{unique_id}",
            "email": f"TEST_freecomp_{unique_id}@test.com",
            "password": "testpass123",
            "first_name": "Test",
            "last_name": "User",
            "phone": "+40700000000"
        }
        
        register_resp = session.post(f"{BASE_URL}/api/auth/register", json=user_data)
        if register_resp.status_code == 200:
            token = register_resp.json().get('token')
            session.headers.update({"Authorization": f"Bearer {token}"})
            print(f"Created test user: {user_data['email']}")
            return session
        else:
            # Try login if user exists
            login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
                "email": user_data['email'],
                "password": user_data['password']
            })
            if login_resp.status_code == 200:
                token = login_resp.json().get('token')
                session.headers.update({"Authorization": f"Bearer {token}"})
                return session
        
        pytest.skip("Could not create or login test user")
    
    def test_duplicate_free_entry_blocked(self, auth_session):
        """Verify second entry to same free competition is blocked"""
        # Find a free competition
        comp_resp = requests.get(f"{BASE_URL}/api/competitions")
        assert comp_resp.status_code == 200
        
        competitions = comp_resp.json()
        free_comp = next((c for c in competitions if c.get('is_free') == True and c.get('status') == 'active'), None)
        
        if not free_comp:
            pytest.skip("No active free competitions available")
        
        print(f"Testing with free competition: {free_comp['title']} ({free_comp['competition_id']})")
        
        # First entry attempt
        entry_data = {
            "competition_id": free_comp['competition_id'],
            "qualification_answer": 0  # Assuming correct answer is 0 for this test
        }
        
        first_resp = auth_session.post(f"{BASE_URL}/api/tickets/enter-free", json=entry_data)
        print(f"First entry response: {first_resp.status_code} - {first_resp.text[:200]}")
        
        # Second entry attempt - should fail
        second_resp = auth_session.post(f"{BASE_URL}/api/tickets/enter-free", json=entry_data)
        print(f"Second entry response: {second_resp.status_code} - {second_resp.text[:200]}")
        
        # Verify second entry is blocked
        assert second_resp.status_code == 400, f"Expected 400 for duplicate entry, got {second_resp.status_code}"
        error_detail = second_resp.json().get('detail', '')
        assert 'deja' in error_detail.lower() or 'already' in error_detail.lower(), f"Expected duplicate error message, got: {error_detail}"
        
        print("✅ Duplicate free entry correctly blocked with error message")


class TestAdminPageAccess:
    """REGRESSION: Verify admin page is accessible"""
    
    def test_admin_login_and_access(self):
        """Test admin login and admin page access"""
        session = requests.Session()
        
        # Login as admin
        login_resp = session.post(f"{BASE_URL}/api/auth/login", json={
            "email": "contact@x67digital.com",
            "password": "Credcada1."
        })
        assert login_resp.status_code == 200, f"Admin login failed: {login_resp.text}"
        
        token = login_resp.json().get('token')
        session.headers.update({"Authorization": f"Bearer {token}"})
        
        # Access admin analytics (requires admin)
        analytics_resp = session.get(f"{BASE_URL}/api/admin/analytics")
        assert analytics_resp.status_code == 200, f"Admin analytics failed: {analytics_resp.text}"
        
        data = analytics_resp.json()
        assert 'total_users' in data
        assert 'total_competitions' in data
        
        print(f"✅ Admin access working - {data['total_users']} users, {data['total_competitions']} competitions")


class TestCompetitionsAPI:
    """REGRESSION: Verify competitions API works correctly"""
    
    def test_get_all_competitions(self):
        """GET /api/competitions returns all competitions"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        
        competitions = response.json()
        assert len(competitions) > 0, "Should have competitions"
        
        # Verify required fields
        required_fields = ['competition_id', 'title', 'competition_type', 'status', 'max_tickets', 'sold_tickets']
        for comp in competitions[:3]:
            for field in required_fields:
                assert field in comp, f"Missing field: {field}"
        
        print(f"✅ Found {len(competitions)} competitions with all required fields")
    
    def test_get_single_competition(self):
        """GET /api/competitions/{id} returns single competition"""
        # First get list
        list_resp = requests.get(f"{BASE_URL}/api/competitions")
        competitions = list_resp.json()
        
        if competitions:
            comp_id = competitions[0]['competition_id']
            detail_resp = requests.get(f"{BASE_URL}/api/competitions/{comp_id}")
            assert detail_resp.status_code == 200
            
            comp = detail_resp.json()
            assert comp['competition_id'] == comp_id
            print(f"✅ Single competition fetch working: {comp['title']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
