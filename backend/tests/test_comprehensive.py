"""
Comprehensive Backend Tests for Zektrix UK Competition Platform
Testing: Auth, Profile, Admin, Competitions, Instant Prizes, Chat, Analytics
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://dynamic-promo-2.preview.emergentagent.com')
if BASE_URL.endswith('/'):
    BASE_URL = BASE_URL.rstrip('/')

# Test credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."

class TestHealth:
    """Basic health check tests"""
    
    def test_health_endpoint(self):
        """Test health endpoint returns 200"""
        response = requests.get(f"{BASE_URL}/api/health", timeout=10)
        assert response.status_code == 200
        print(f"✓ Health check passed: {response.json()}")
    
    def test_api_root(self):
        """Test API root returns info"""
        response = requests.get(f"{BASE_URL}/api/", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "message" in data or "name" in data or "status" in data
        print(f"✓ API root accessible")


class TestAuthentication:
    """Auth flow tests - login, register, session"""
    
    def test_admin_login_success(self):
        """Test admin login with correct credentials"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["email"] == ADMIN_EMAIL
        assert data["user"]["role"] == "admin"
        print(f"✓ Admin login successful, token received")
        return data["token"]
    
    def test_login_invalid_credentials(self):
        """Test login with wrong password"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": "wrongpassword"},
            timeout=10
        )
        assert response.status_code == 401
        print(f"✓ Invalid credentials properly rejected (401)")
    
    def test_auth_me_without_token(self):
        """Test /auth/me without token returns 401"""
        response = requests.get(f"{BASE_URL}/api/auth/me", timeout=10)
        assert response.status_code in [401, 403]
        print(f"✓ /auth/me properly requires authentication")
    
    def test_auth_me_with_valid_token(self):
        """Test /auth/me with valid admin token"""
        # First login
        login_resp = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        token = login_resp.json()["token"]
        
        # Then check /auth/me
        response = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == ADMIN_EMAIL
        print(f"✓ /auth/me returns correct user data")


class TestProfileUpdate:
    """Profile update tests - PUT /api/auth/profile"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        return response.json()["token"]
    
    def test_profile_update_first_name(self, admin_token):
        """Test updating first_name field"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"first_name": "TestFirstName"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200, f"Profile update failed: {response.text}"
        data = response.json()
        assert data["first_name"] == "TestFirstName"
        print(f"✓ Profile first_name update successful")
    
    def test_profile_update_last_name(self, admin_token):
        """Test updating last_name field"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"last_name": "TestLastName"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["last_name"] == "TestLastName"
        print(f"✓ Profile last_name update successful")
    
    def test_profile_update_phone(self, admin_token):
        """Test updating phone field"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"phone": "+44 123456789"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["phone"] == "+44 123456789"
        print(f"✓ Profile phone update successful")
    
    def test_profile_update_multiple_fields(self, admin_token):
        """Test updating multiple fields at once"""
        update_data = {
            "first_name": "Admin",
            "last_name": "Test",
            "phone": "+40 733569338"
        }
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json=update_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert data["first_name"] == update_data["first_name"]
        assert data["last_name"] == update_data["last_name"]
        assert data["phone"] == update_data["phone"]
        print(f"✓ Profile multi-field update successful")
    
    def test_profile_update_without_auth(self):
        """Test profile update without authentication"""
        response = requests.put(
            f"{BASE_URL}/api/auth/profile",
            json={"first_name": "Test"},
            timeout=10
        )
        assert response.status_code in [401, 403]
        print(f"✓ Profile update properly requires authentication")


class TestCompetitions:
    """Competition endpoints tests"""
    
    def test_get_competitions(self):
        """Test GET /api/competitions returns competition list"""
        response = requests.get(f"{BASE_URL}/api/competitions", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/competitions returned {len(data)} competitions")
        return data
    
    def test_competition_has_required_fields(self):
        """Test competitions have all required fields"""
        response = requests.get(f"{BASE_URL}/api/competitions", timeout=10)
        data = response.json()
        
        if len(data) > 0:
            comp = data[0]
            required_fields = ["competition_id", "title", "description", "ticket_price", 
                            "max_tickets", "sold_tickets", "status"]
            for field in required_fields:
                assert field in comp, f"Missing field: {field}"
            print(f"✓ Competition has all required fields")
        else:
            print("⚠ No competitions to check fields")
    
    def test_get_competition_by_id(self):
        """Test GET /api/competitions/{id} returns specific competition"""
        # First get list to get an ID
        list_resp = requests.get(f"{BASE_URL}/api/competitions", timeout=10)
        competitions = list_resp.json()
        
        if len(competitions) > 0:
            comp_id = competitions[0]["competition_id"]
            response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}", timeout=10)
            assert response.status_code == 200
            data = response.json()
            assert data["competition_id"] == comp_id
            print(f"✓ GET /api/competitions/{comp_id} successful")
        else:
            pytest.skip("No competitions available to test")
    
    def test_competition_instant_prizes_field(self):
        """Test competitions can have instant_prizes field"""
        response = requests.get(f"{BASE_URL}/api/competitions", timeout=10)
        data = response.json()
        
        # Check if any competition has instant_prizes
        has_prizes = any(comp.get("instant_prizes") for comp in data)
        if has_prizes:
            for comp in data:
                if comp.get("instant_prizes"):
                    prizes = comp["instant_prizes"]
                    assert isinstance(prizes, list)
                    print(f"✓ Competition '{comp['title']}' has {len(prizes)} instant prizes")
                    break
        else:
            print("⚠ No competitions with instant_prizes found (feature available)")


class TestAdminEndpoints:
    """Admin panel endpoints tests"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        return response.json()["token"]
    
    def test_admin_stats(self, admin_token):
        """Test GET /api/admin/stats returns admin statistics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        # Check for expected fields
        expected_fields = ["active_competitions", "total_users", "total_tickets"]
        for field in expected_fields:
            assert field in data, f"Missing stats field: {field}"
        print(f"✓ Admin stats: {data.get('active_competitions', 0)} active competitions, {data.get('total_users', 0)} users")
    
    def test_admin_analytics(self, admin_token):
        """Test GET /api/admin/analytics returns analytics data"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data
        assert "total_users" in data
        assert "revenue_by_day" in data
        assert "top_competitions" in data
        print(f"✓ Admin analytics returned in {elapsed:.2f}s with {data.get('total_revenue', 0):.2f} total revenue")
    
    def test_admin_users(self, admin_token):
        """Test GET /api/admin/users returns user list"""
        response = requests.get(
            f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin users endpoint returned {len(data)} users")
    
    def test_admin_tickets(self, admin_token):
        """Test GET /api/admin/tickets returns ticket list quickly"""
        start = time.time()
        response = requests.get(
            f"{BASE_URL}/api/admin/tickets",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        elapsed = time.time() - start
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert elapsed < 3.0, f"Tickets endpoint too slow: {elapsed:.2f}s"
        print(f"✓ Admin tickets returned {len(data)} tickets in {elapsed:.2f}s")
    
    def test_admin_without_auth(self):
        """Test admin endpoints require authentication"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", timeout=10)
        assert response.status_code in [401, 403]
        print(f"✓ Admin endpoints properly require authentication")


class TestAdminCompetitionCRUD:
    """Admin competition creation with instant prizes"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        return response.json()["token"]
    
    def test_create_competition_with_instant_prizes(self, admin_token):
        """Test creating competition with instant prizes"""
        comp_data = {
            "title": "TEST Competition with Instant Prizes",
            "description": "Test competition for automated testing - will be deleted",
            "ticket_price": 1.99,
            "max_tickets": 100,
            "competition_type": "instant_win",
            "category": "tech",
            "image_url": "https://images.unsplash.com/photo-1557683316-973673baf926?w=800",
            "prize_description": "Test Prize",
            "instant_prizes": [
                {"percentage": 25, "prize_name": "£25 Cash", "prize_description": "Quarter milestone prize"},
                {"percentage": 50, "prize_name": "£50 Cash", "prize_description": "Half milestone prize"},
                {"percentage": 75, "prize_name": "£100 Cash", "prize_description": "Three quarter milestone prize"}
            ],
            "qualification_question": {
                "question": "Is this a test?",
                "options": ["Yes", "No"],
                "correct_answer": 0
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/competitions",
            json=comp_data,
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=15
        )
        
        # Check creation was successful
        assert response.status_code == 200, f"Create competition failed: {response.text}"
        data = response.json()
        assert data["title"] == comp_data["title"]
        assert data.get("instant_prizes") is not None
        assert len(data["instant_prizes"]) == 3
        
        comp_id = data["competition_id"]
        print(f"✓ Competition created with ID: {comp_id} and 3 instant prizes")
        
        # Clean up - delete the test competition
        del_response = requests.delete(
            f"{BASE_URL}/api/admin/competitions/{comp_id}",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        if del_response.status_code == 200:
            print(f"✓ Test competition deleted")


class TestChat:
    """Chat widget and FAQ tests"""
    
    def test_chat_faq_endpoint(self):
        """Test GET /api/chat/faq returns FAQ items"""
        response = requests.get(f"{BASE_URL}/api/chat/faq", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0, "FAQ should have items"
        
        # Check FAQ structure
        faq = data[0]
        assert "keyword" in faq
        assert "question" in faq
        print(f"✓ Chat FAQ returned {len(data)} items")
    
    @pytest.fixture
    def admin_token(self):
        """Get admin auth token"""
        response = requests.post(
            f"{BASE_URL}/api/auth/login",
            json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            timeout=10
        )
        return response.json()["token"]
    
    def test_chat_history_requires_auth(self):
        """Test /api/chat/history requires authentication"""
        response = requests.get(f"{BASE_URL}/api/chat/history", timeout=10)
        assert response.status_code in [401, 403]
        print(f"✓ Chat history properly requires authentication")
    
    def test_admin_chat_messages(self, admin_token):
        """Test GET /api/admin/chat/messages returns chat messages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/chat/messages",
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=10
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Admin chat messages returned {len(data)} messages")


class TestWinners:
    """Winners endpoint tests"""
    
    def test_get_winners(self):
        """Test GET /api/winners returns winners list"""
        response = requests.get(f"{BASE_URL}/api/winners", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ Winners endpoint returned {len(data)} winners")


class TestSettingsAndLiveStatus:
    """Settings and live status tests"""
    
    def test_tiktok_live_status(self):
        """Test GET /api/settings/tiktok-live returns live status"""
        response = requests.get(f"{BASE_URL}/api/settings/tiktok-live", timeout=10)
        assert response.status_code == 200
        data = response.json()
        assert "is_live" in data
        print(f"✓ TikTok live status: {data.get('is_live', False)}")


class TestPasswordReset:
    """Password reset flow tests"""
    
    def test_password_reset_request(self):
        """Test POST /api/auth/request-password-reset"""
        response = requests.post(
            f"{BASE_URL}/api/auth/request-password-reset",
            json={"email": "nonexistent@test.com"},
            timeout=10
        )
        # Should always return success to prevent email enumeration
        assert response.status_code == 200
        print(f"✓ Password reset request handled correctly")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
