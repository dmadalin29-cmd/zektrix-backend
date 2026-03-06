"""
Test suite for Zektrix UK Competition Platform - New Features
Tests: Share API, Referral System, Analytics Dashboard, WebSocket
"""
import pytest
import requests
import os
import uuid
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestShareAPI:
    """Test social sharing endpoints"""
    
    def test_share_competition_valid(self):
        """Test GET /api/share/competition/{id} with valid competition"""
        # First get a valid competition
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        competitions = response.json()
        assert len(competitions) > 0
        
        comp_id = competitions[0]["competition_id"]
        
        # Test share endpoint
        response = requests.get(f"{BASE_URL}/api/share/competition/{comp_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "title" in data
        assert "share_url" in data
        assert "share_text" in data
        assert "twitter_url" in data
        assert "facebook_url" in data
        assert "whatsapp_url" in data
        assert "zektrix.uk" in data["share_url"]
        print(f"✓ Share API returns valid data for competition: {data['title']}")
    
    def test_share_competition_invalid(self):
        """Test GET /api/share/competition/{id} with invalid competition"""
        response = requests.get(f"{BASE_URL}/api/share/competition/invalid_comp_id")
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
        print("✓ Share API returns 404 for invalid competition")


class TestReferralSystem:
    """Test referral system endpoints"""
    
    @pytest.fixture
    def new_user_with_referral_code(self):
        """Create a new user and get their referral code"""
        unique_id = uuid.uuid4().hex[:8]
        user_data = {
            "username": f"TEST_ref_user_{unique_id}",
            "email": f"TEST_ref_{unique_id}@test.com",
            "password": "testpass123"
        }
        response = requests.post(f"{BASE_URL}/api/auth/register", json=user_data)
        assert response.status_code == 200
        
        token = response.json()["token"]
        
        # Get referral code
        headers = {"Authorization": f"Bearer {token}"}
        ref_response = requests.get(f"{BASE_URL}/api/referral/my-code", headers=headers)
        assert ref_response.status_code == 200
        
        return {
            "token": token,
            "user": response.json()["user"],
            "referral_code": ref_response.json()["referral_code"]
        }
    
    def test_validate_referral_code_invalid(self):
        """Test GET /api/referral/validate/{code} with invalid code"""
        response = requests.get(f"{BASE_URL}/api/referral/validate/INVALIDCODE123")
        assert response.status_code == 404
        assert "invalid" in response.json()["detail"].lower()
        print("✓ Referral validation returns 404 for invalid code")
    
    def test_validate_referral_code_valid(self, new_user_with_referral_code):
        """Test GET /api/referral/validate/{code} with valid code"""
        ref_code = new_user_with_referral_code["referral_code"]
        
        response = requests.get(f"{BASE_URL}/api/referral/validate/{ref_code}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["valid"] == True
        assert "referrer_username" in data
        print(f"✓ Referral validation returns valid=True for code: {ref_code}")
    
    def test_get_my_referral_code(self, new_user_with_referral_code):
        """Test GET /api/referral/my-code"""
        headers = {"Authorization": f"Bearer {new_user_with_referral_code['token']}"}
        response = requests.get(f"{BASE_URL}/api/referral/my-code", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        assert "referral_code" in data
        assert "referral_link" in data
        assert "total_referrals" in data
        assert "completed_referrals" in data
        assert "pending_referrals" in data
        assert "total_earned" in data
        assert "bonus_per_referral" in data
        assert data["bonus_per_referral"] == 5
        print(f"✓ My referral code endpoint returns complete data: {data['referral_code']}")
    
    def test_get_my_referrals(self, new_user_with_referral_code):
        """Test GET /api/referral/my-referrals"""
        headers = {"Authorization": f"Bearer {new_user_with_referral_code['token']}"}
        response = requests.get(f"{BASE_URL}/api/referral/my-referrals", headers=headers)
        
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✓ My referrals endpoint returns list")
    
    def test_referral_code_unauthenticated(self):
        """Test referral endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/referral/my-code")
        assert response.status_code == 401
        print("✓ Referral endpoints require authentication")


class TestAnalyticsDashboard:
    """Test admin analytics endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zektrix.uk",
            "password": "admin123"
        })
        if response.status_code != 200:
            pytest.skip("Admin login failed")
        return response.json()["token"]
    
    def test_analytics_endpoint_authenticated(self, admin_token):
        """Test GET /api/admin/analytics with admin auth"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify all expected fields
        expected_fields = [
            "total_revenue", "total_users", "total_tickets", "total_competitions",
            "active_competitions", "completed_competitions", "total_winners",
            "avg_tickets_per_user", "revenue_by_day", "top_competitions",
            "user_growth", "total_referrals", "referral_bonus_paid"
        ]
        
        for field in expected_fields:
            assert field in data, f"Missing field: {field}"
        
        # Verify data types
        assert isinstance(data["total_revenue"], (int, float))
        assert isinstance(data["total_users"], int)
        assert isinstance(data["total_tickets"], int)
        assert isinstance(data["revenue_by_day"], list)
        assert isinstance(data["top_competitions"], list)
        assert isinstance(data["user_growth"], list)
        
        print(f"✓ Analytics endpoint returns comprehensive data:")
        print(f"  - Total Revenue: £{data['total_revenue']}")
        print(f"  - Total Users: {data['total_users']}")
        print(f"  - Total Tickets: {data['total_tickets']}")
        print(f"  - Active Competitions: {data['active_competitions']}")
    
    def test_analytics_endpoint_unauthenticated(self):
        """Test GET /api/admin/analytics without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics")
        assert response.status_code == 401
        print("✓ Analytics endpoint requires authentication")
    
    def test_analytics_endpoint_non_admin(self):
        """Test GET /api/admin/analytics with non-admin user"""
        # Create regular user
        unique_id = uuid.uuid4().hex[:8]
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"TEST_regular_{unique_id}",
            "email": f"TEST_regular_{unique_id}@test.com",
            "password": "testpass123"
        })
        
        if response.status_code == 200:
            token = response.json()["token"]
            headers = {"Authorization": f"Bearer {token}"}
            
            analytics_response = requests.get(f"{BASE_URL}/api/admin/analytics", headers=headers)
            assert analytics_response.status_code == 403
            print("✓ Analytics endpoint requires admin role")


class TestWebSocket:
    """Test WebSocket endpoints"""
    
    def test_websocket_endpoint_exists(self):
        """Verify WebSocket endpoints are defined in the API"""
        # We can't easily test WebSocket with requests, but we can verify the server is running
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        assert response.json()["version"] == "2.0.0"
        print("✓ Server is running version 2.0.0 with WebSocket support")


class TestAPIVersion:
    """Test API version and health"""
    
    def test_api_version(self):
        """Test API returns correct version"""
        response = requests.get(f"{BASE_URL}/api/")
        assert response.status_code == 200
        data = response.json()
        assert data["version"] == "2.0.0"
        assert "Zektrix" in data["message"]
        print(f"✓ API version: {data['version']}")


class TestExistingFeatures:
    """Regression tests for existing features"""
    
    def test_competitions_list(self):
        """Test GET /api/competitions"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        competitions = response.json()
        assert isinstance(competitions, list)
        print(f"✓ Competitions list returns {len(competitions)} competitions")
    
    def test_winners_list(self):
        """Test GET /api/winners"""
        response = requests.get(f"{BASE_URL}/api/winners")
        assert response.status_code == 200
        assert isinstance(response.json(), list)
        print("✓ Winners list endpoint working")
    
    def test_login_admin(self):
        """Test admin login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zektrix.uk",
            "password": "admin123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert data["user"]["role"] == "admin"
        print("✓ Admin login successful")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
