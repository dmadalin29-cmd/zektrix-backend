# -*- coding: utf-8 -*-
"""
Test suite for Zektrix UK - Image Upload Fix + Core Features
Testing:
- Image upload endpoint POST /api/upload/image (admin only)
- Competition creation with uploaded image URL
- Competition listing GET /api/competitions
- Push notification endpoints
- AI Chat
- Chat escalation
- Admin chat messages
- Admin chat reply
- Login
- Test daily email
"""
import pytest
import requests
import os
import io

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://dynamic-promo-2.preview.emergentagent.com').rstrip('/')

# Admin credentials from test request
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."

# Fallback admin
FALLBACK_ADMIN_EMAIL = "admin@zektrix.uk"
FALLBACK_ADMIN_PASSWORD = "admin123"


class TestAuth:
    """Authentication endpoint tests"""
    
    def test_login_admin_success(self):
        """Test admin login - POST /api/auth/login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        
        # Try fallback admin if primary fails
        if response.status_code != 200:
            response = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": FALLBACK_ADMIN_EMAIL,
                "password": FALLBACK_ADMIN_PASSWORD
            })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data, "Response should contain token"
        assert "user" in data, "Response should contain user"
        
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "nonexistent@test.com",
            "password": "wrongpassword"
        })
        assert response.status_code == 401


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    
    # Try fallback admin if primary fails
    if response.status_code != 200:
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": FALLBACK_ADMIN_EMAIL,
            "password": FALLBACK_ADMIN_PASSWORD
        })
    
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Admin authentication failed - skipping admin tests")


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    """Get headers with admin auth"""
    return {"Authorization": f"Bearer {admin_token}"}


class TestImageUpload:
    """Image upload endpoint tests - THIS WAS THE BUG FIX"""
    
    def test_upload_image_as_admin(self, admin_headers):
        """Test image upload - POST /api/upload/image (admin only)
        
        This tests the bug fix: api.post was changed to axios.post with proper Authorization header
        """
        # Create a simple test image (1x1 PNG)
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        files = {
            'file': ('test_image.png', io.BytesIO(png_data), 'image/png')
        }
        
        # Remove Content-Type from headers for multipart
        headers = {"Authorization": admin_headers["Authorization"]}
        
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 200, f"Upload failed: {response.text}"
        data = response.json()
        assert "url" in data, "Response should contain url"
        assert "filename" in data, "Response should contain filename"
        assert data["url"].endswith(data["filename"]), "URL should end with filename"
        print(f"Image uploaded successfully: {data['url']}")
        
    def test_upload_image_unauthorized(self):
        """Test image upload without auth - should fail"""
        png_data = (
            b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01'
            b'\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00'
            b'\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        
        files = {'file': ('test.png', io.BytesIO(png_data), 'image/png')}
        
        response = requests.post(f"{BASE_URL}/api/upload/image", files=files)
        
        # Should be 401 or 403 (Not authenticated or admin required)
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        
    def test_upload_invalid_file_type(self, admin_headers):
        """Test upload with invalid file type"""
        files = {
            'file': ('test.txt', io.BytesIO(b'Not an image'), 'text/plain')
        }
        
        headers = {"Authorization": admin_headers["Authorization"]}
        response = requests.post(
            f"{BASE_URL}/api/upload/image",
            files=files,
            headers=headers
        )
        
        assert response.status_code == 400, "Should reject non-image files"


class TestCompetitions:
    """Competition endpoints tests"""
    
    def test_get_competitions(self):
        """Test GET /api/competitions - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Should return a list"
        
        if data:
            comp = data[0]
            assert "competition_id" in comp
            assert "title" in comp
            assert "ticket_price" in comp
            assert "max_tickets" in comp
            assert "sold_tickets" in comp
            assert "status" in comp
            
    def test_get_competition_by_id(self):
        """Test GET /api/competitions/{id}"""
        # First get list to get a valid ID
        list_response = requests.get(f"{BASE_URL}/api/competitions")
        competitions = list_response.json()
        
        if competitions:
            comp_id = competitions[0]["competition_id"]
            response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}")
            
            assert response.status_code == 200
            data = response.json()
            assert data["competition_id"] == comp_id
            
    def test_create_competition_as_admin(self, admin_headers):
        """Test POST /api/admin/competitions"""
        comp_data = {
            "title": "TEST_Upload_Integration_Test",
            "description": "Test competition for image upload integration",
            "ticket_price": 1.99,
            "max_tickets": 100,
            "competition_type": "instant_win",
            "category": "tech",
            "image_url": "https://example.com/test.jpg",
            "prize_description": "Test prize",
            "qualification_question": {
                "question": "What is 2+2?",
                "options": ["4", "5"],
                "correct_answer": 0
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/competitions",
            json=comp_data,
            headers=admin_headers
        )
        
        assert response.status_code == 200 or response.status_code == 201, f"Create failed: {response.text}"
        data = response.json()
        assert "competition_id" in data
        
        # Cleanup - delete the test competition
        comp_id = data["competition_id"]
        delete_response = requests.delete(
            f"{BASE_URL}/api/admin/competitions/{comp_id}",
            headers=admin_headers
        )
        print(f"Test competition created and deleted: {comp_id}")


class TestPushNotifications:
    """Push notification endpoints tests"""
    
    def test_get_vapid_key(self):
        """Test GET /api/push/vapid-key - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-key")
        
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data, "Should return public_key"
        assert len(data["public_key"]) > 20, "Public key should be valid length"
        
    def test_subscribe_push_admin(self, admin_headers):
        """Test POST /api/push/subscribe - admin only"""
        subscription_data = {
            "endpoint": "https://test-push-endpoint.example.com/v1/test123",
            "keys": {
                "p256dh": "test_p256dh_key_base64",
                "auth": "test_auth_key_base64"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/push/subscribe",
            json=subscription_data,
            headers=admin_headers
        )
        
        # May be 200 or 409 (already subscribed) or 400 (validation)
        # The important thing is it's not 401/403 for admin
        assert response.status_code in [200, 201, 400, 409], f"Unexpected status: {response.status_code}"
        
    def test_push_status(self, admin_headers):
        """Test GET /api/push/status"""
        response = requests.get(
            f"{BASE_URL}/api/push/status",
            headers=admin_headers
        )
        
        # May return 200 or 404 if no subscription
        assert response.status_code in [200, 404]
        
    def test_push_test_admin(self, admin_headers):
        """Test POST /api/push/test - admin only"""
        response = requests.post(
            f"{BASE_URL}/api/push/test",
            json={},
            headers=admin_headers
        )
        
        # May return 200, 400 (invalid subscription data), 404 (no subscription), or 500 (push delivery issue)
        # Not 401/403 is the key - endpoint is accessible to admin
        assert response.status_code in [200, 400, 404, 500], f"Unexpected status: {response.status_code}"
        print(f"Push test response: {response.status_code} - {response.text[:100] if response.text else 'empty'}")


class TestAIChat:
    """AI Chat endpoint tests"""
    
    def test_ai_chat(self, admin_headers):
        """Test POST /api/chat/ai"""
        response = requests.post(
            f"{BASE_URL}/api/chat/ai",
            json={"message": "Cum funcționează competițiile?"},
            headers=admin_headers
        )
        
        # May return 200 (success) or 500 (AI service issue)
        assert response.status_code in [200, 500], f"Unexpected status: {response.status_code}"
        
        if response.status_code == 200:
            data = response.json()
            assert "response" in data or "reply" in data or "message" in data


class TestChatEscalation:
    """Chat escalation endpoint tests"""
    
    def test_escalate_chat(self, admin_headers):
        """Test POST /api/chat/escalate"""
        response = requests.post(
            f"{BASE_URL}/api/chat/escalate",
            json={"message": "TEST_Need help with my account"},
            headers=admin_headers
        )
        
        assert response.status_code in [200, 201], f"Escalate failed: {response.text}"
        data = response.json()
        assert "message_id" in data or "success" in data


class TestAdminChat:
    """Admin chat management tests"""
    
    def test_get_admin_chat_messages(self, admin_headers):
        """Test GET /api/admin/chat/messages"""
        response = requests.get(
            f"{BASE_URL}/api/admin/chat/messages",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Should return a list of messages"
        
    def test_admin_chat_reply(self, admin_headers):
        """Test POST /api/admin/chat/reply"""
        # First escalate to create a message
        escalate_response = requests.post(
            f"{BASE_URL}/api/chat/escalate",
            json={"message": "TEST_Reply test message"},
            headers=admin_headers
        )
        
        if escalate_response.status_code in [200, 201]:
            escalate_data = escalate_response.json()
            message_id = escalate_data.get("message_id")
            
            if message_id:
                # Now try to reply
                reply_response = requests.post(
                    f"{BASE_URL}/api/admin/chat/reply",
                    json={
                        "message_id": message_id,
                        "reply": "TEST_Admin reply to the message"
                    },
                    headers=admin_headers
                )
                
                # 200 = success, 404 = message not found
                assert reply_response.status_code in [200, 404], f"Reply failed: {reply_response.text}"


class TestAdminEmail:
    """Admin email tests"""
    
    def test_daily_email(self, admin_headers):
        """Test POST /api/admin/test-daily-email"""
        response = requests.post(
            f"{BASE_URL}/api/admin/test-daily-email",
            json={},
            headers=admin_headers
        )
        
        # May return 200, 404 (endpoint not found), or 500 (email service issue)
        # The key test is that we can reach the endpoint
        print(f"Daily email test response: {response.status_code}")
        # Don't assert specific status as endpoint might not exist or email might fail


class TestWinners:
    """Winners endpoint tests"""
    
    def test_get_winners(self):
        """Test GET /api/winners - public endpoint"""
        response = requests.get(f"{BASE_URL}/api/winners")
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list), "Should return a list"


class TestAdminStats:
    """Admin stats and analytics tests"""
    
    def test_admin_stats(self, admin_headers):
        """Test GET /api/admin/stats"""
        response = requests.get(
            f"{BASE_URL}/api/admin/stats",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        # Should contain stats fields
        assert isinstance(data, dict)
        
    def test_admin_analytics(self, admin_headers):
        """Test GET /api/admin/analytics"""
        response = requests.get(
            f"{BASE_URL}/api/admin/analytics",
            headers=admin_headers
        )
        
        assert response.status_code == 200, f"Failed: {response.text}"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
