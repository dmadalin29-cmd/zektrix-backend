"""
Test Bug Fixes for Zektrix UK Competition Platform
Testing: Google Auth, Chat duplicates, Push notifications
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vapid-sync-test.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "admin@zektrix.uk"
ADMIN_PASSWORD = "admin123"

class TestAuthEndpoints:
    """Test authentication endpoints"""
    
    def test_login_admin(self):
        """Admin login works with email/password"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        data = response.json()
        assert "token" in data
        assert "user" in data
        assert data["user"]["role"] == "admin"
        print(f"Admin login successful - user: {data['user']['username']}")
        return data["token"]
    
    def test_auth_session_invalid(self):
        """Auth session endpoint returns 401 for invalid session_id"""
        response = requests.get(f"{BASE_URL}/api/auth/session", params={
            "session_id": "invalid_test_session"
        })
        assert response.status_code == 401
        print("Auth session correctly rejects invalid session_id")
    
    def test_auth_me_requires_token(self):
        """Auth me endpoint requires valid token"""
        response = requests.get(f"{BASE_URL}/api/auth/me")
        assert response.status_code == 401
        print("Auth me correctly requires authentication")
    
    def test_auth_me_with_valid_token(self):
        """Auth me returns user data with valid token"""
        # Get token first
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        token = login_resp.json()["token"]
        
        # Test /api/auth/me
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        print(f"Auth me successful - email: {data['email']}")


class TestChatEndpoints:
    """Test chat endpoints - AI chat, escalation, history"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_chat_ai_endpoint(self, admin_token):
        """Chat AI endpoint returns response"""
        response = requests.post(f"{BASE_URL}/api/chat/ai", 
            json={"message": "Test question"},
            headers={"Authorization": f"Bearer {admin_token}"},
            timeout=30
        )
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "session_id" in data
        print(f"AI chat response received: {data['response'][:50]}...")
    
    def test_chat_escalate_endpoint(self, admin_token):
        """Chat escalate endpoint creates message"""
        response = requests.post(f"{BASE_URL}/api/chat/escalate",
            json={"message": "Test escalation message"},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message_id" in data
        print(f"Chat escalation successful - message_id: {data['message_id']}")
    
    def test_chat_history_no_duplicates(self, admin_token):
        """Chat history returns no duplicate messages"""
        response = requests.get(f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        
        # Check for duplicates
        message_ids = [m.get("message_id") for m in data if m.get("message_id")]
        unique_ids = set(message_ids)
        
        assert len(message_ids) == len(unique_ids), f"Duplicate messages found! {len(message_ids)} total, {len(unique_ids)} unique"
        print(f"Chat history has {len(data)} messages, no duplicates")
    
    def test_admin_chat_messages(self, admin_token):
        """Admin chat messages endpoint returns correct data"""
        response = requests.get(f"{BASE_URL}/api/admin/chat/messages",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        
        # Check for duplicates in admin messages too
        if data:
            message_ids = [m.get("message_id") for m in data if m.get("message_id")]
            unique_ids = set(message_ids)
            assert len(message_ids) == len(unique_ids), "Duplicate admin messages found!"
        
        print(f"Admin chat has {len(data)} messages, no duplicates")


class TestPushNotifications:
    """Test push notification endpoints"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token for authenticated tests"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_vapid_key_endpoint(self):
        """VAPID key endpoint returns public key"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        assert len(data["public_key"]) > 50  # VAPID key should be substantial
        print(f"VAPID public key: {data['public_key'][:30]}...")
    
    def test_push_subscribe_requires_admin(self, admin_token):
        """Push subscribe endpoint works for admin"""
        # Test with mock subscription data
        response = requests.post(f"{BASE_URL}/api/push/subscribe",
            json={
                "endpoint": "https://test.push.endpoint/test",
                "keys": {
                    "p256dh": "test_p256dh_key",
                    "auth": "test_auth_key"
                }
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        print("Push subscribe endpoint works for admin")


class TestAdminAccess:
    """Test admin panel access"""
    
    @pytest.fixture
    def admin_token(self):
        """Get admin token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        return response.json()["token"]
    
    def test_admin_stats(self, admin_token):
        """Admin stats endpoint returns data"""
        response = requests.get(f"{BASE_URL}/api/admin/stats",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data or "active_competitions" in data
        print(f"Admin stats: {data}")
    
    def test_admin_users(self, admin_token):
        """Admin users endpoint returns user list"""
        response = requests.get(f"{BASE_URL}/api/admin/users",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin can see {len(data)} users")
    
    def test_admin_tickets(self, admin_token):
        """Admin tickets endpoint returns ticket list"""
        response = requests.get(f"{BASE_URL}/api/admin/tickets",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin can see {len(data)} tickets")


class TestCompetitionsAPI:
    """Test competitions API"""
    
    def test_get_competitions(self):
        """Get competitions returns list"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Found {len(data)} competitions")
    
    def test_competition_types(self):
        """Competitions have correct type field"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        data = response.json()
        
        for comp in data:
            assert "competition_type" in comp
            assert comp["competition_type"] in ["instant_win", "classic"]
        print("All competitions have valid competition_type")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
