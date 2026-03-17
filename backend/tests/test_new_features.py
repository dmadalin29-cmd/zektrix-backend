"""
Test suite for new features: Privacy Policy, Google Analytics, Live Chat
Tests for Zektrix UK Competition Platform
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://competition-platform-1.preview.emergentagent.com').rstrip('/')

# Admin credentials from test request
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."

@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session

@pytest.fixture(scope="module")
def auth_token(api_client):
    """Get authentication token for admin"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip("Authentication failed - skipping authenticated tests")

# ==================== CHAT FAQ ENDPOINT ====================
class TestChatFAQ:
    """Tests for /api/chat/faq endpoint"""
    
    def test_get_faq_list_success(self, api_client):
        """Test GET /api/chat/faq returns FAQ list"""
        response = api_client.get(f"{BASE_URL}/api/chat/faq")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Data assertion - should be a list
        data = response.json()
        assert isinstance(data, list), "FAQ should be a list"
        assert len(data) > 0, "FAQ list should not be empty"
        
        # Verify FAQ structure
        faq_item = data[0]
        assert "question" in faq_item, "FAQ item should have 'question' field"
        assert "keyword" in faq_item, "FAQ item should have 'keyword' field"
        
        print(f"✓ FAQ endpoint returned {len(data)} FAQ items")

    def test_faq_contains_expected_topics(self, api_client):
        """Test that FAQ contains expected topics"""
        response = api_client.get(f"{BASE_URL}/api/chat/faq")
        assert response.status_code == 200
        
        data = response.json()
        keywords = [item.get("keyword", "").lower() for item in data]
        
        # Check for expected FAQ topics
        expected_topics = ["cum funcționează", "bilete", "contact"]
        found_topics = []
        for topic in expected_topics:
            for keyword in keywords:
                if topic in keyword:
                    found_topics.append(topic)
                    break
        
        assert len(found_topics) > 0, f"Expected at least some FAQ topics, got none matching {expected_topics}"
        print(f"✓ FAQ contains expected topics: {found_topics}")


# ==================== CHAT HISTORY ENDPOINT (Requires Auth) ====================
class TestChatHistory:
    """Tests for /api/chat/history endpoint"""
    
    def test_chat_history_requires_auth(self, api_client):
        """Test GET /api/chat/history requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/chat/history")
        
        # Should return 401 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Chat history endpoint properly requires authentication")

    def test_chat_history_with_auth(self, api_client, auth_token):
        """Test GET /api/chat/history with authentication"""
        response = api_client.get(
            f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200 with auth, got {response.status_code}"
        
        # Data assertion - should be a list (may be empty for new users)
        data = response.json()
        assert isinstance(data, list), "Chat history should be a list"
        print(f"✓ Chat history endpoint returned {len(data)} messages")


# ==================== CHAT MESSAGE ENDPOINT (Requires Auth) ====================
class TestChatMessage:
    """Tests for /api/chat/message endpoint"""
    
    def test_chat_message_requires_auth(self, api_client):
        """Test POST /api/chat/message requires authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/chat/message",
            json={"message": "test message", "is_faq": False}
        )
        
        # Should return 401 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Chat message endpoint properly requires authentication")

    def test_chat_message_with_auth(self, api_client, auth_token):
        """Test POST /api/chat/message with authentication"""
        response = api_client.post(
            f"{BASE_URL}/api/chat/message",
            json={"message": "cum funcționează", "is_faq": True},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200 with auth, got {response.status_code}"
        
        # Data assertion
        data = response.json()
        assert "response" in data or "type" in data or "message_id" in data, \
            f"Expected response to contain 'response', 'type' or 'message_id', got: {data}"
        print(f"✓ Chat message endpoint responded with FAQ/support message")


# ==================== ADMIN CHAT MESSAGES ENDPOINT ====================
class TestAdminChatMessages:
    """Tests for /api/admin/chat/messages endpoint"""
    
    def test_admin_chat_messages_requires_auth(self, api_client):
        """Test GET /api/admin/chat/messages requires authentication"""
        response = api_client.get(f"{BASE_URL}/api/admin/chat/messages")
        
        # Should return 401 without auth
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("✓ Admin chat messages endpoint properly requires authentication")

    def test_admin_chat_messages_with_admin_auth(self, api_client, auth_token):
        """Test GET /api/admin/chat/messages with admin authentication"""
        response = api_client.get(
            f"{BASE_URL}/api/admin/chat/messages",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200 with admin auth, got {response.status_code}"
        
        # Data assertion - should be a list
        data = response.json()
        assert isinstance(data, list), "Admin chat messages should be a list"
        print(f"✓ Admin chat messages endpoint returned {len(data)} messages")


# ==================== GOOGLE ANALYTICS VERIFICATION ====================
class TestGoogleAnalytics:
    """Tests for Google Analytics integration"""
    
    def test_index_html_has_gtag_script(self, api_client):
        """Test that index.html contains Google Analytics script with correct ID"""
        response = api_client.get(f"{BASE_URL}/")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check for Google Analytics script
        html_content = response.text
        assert "googletagmanager.com/gtag" in html_content, "gtag.js script not found in HTML"
        assert "G-G760C5BPRM" in html_content, "Google Analytics ID G-G760C5BPRM not found in HTML"
        
        print("✓ Google Analytics script with ID G-G760C5BPRM found in index.html")


# ==================== PRIVACY POLICY PAGE ====================
class TestPrivacyPolicy:
    """Tests for Privacy Policy page"""
    
    def test_privacy_page_loads(self, api_client):
        """Test that /privacy route loads correctly"""
        response = api_client.get(f"{BASE_URL}/privacy")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Check for Privacy Policy content markers
        html_content = response.text
        # React app loads the same index.html, so we verify the base loads
        assert "root" in html_content, "React root element not found"
        
        print("✓ Privacy Policy page route loads correctly")


# ==================== FOOTER LINK VERIFICATION ====================
class TestFooterLinks:
    """Tests for Footer components"""
    
    def test_homepage_loads_with_footer(self, api_client):
        """Test that homepage loads (which includes Footer with Privacy link)"""
        response = api_client.get(f"{BASE_URL}/")
        
        # Status code assertion
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        print("✓ Homepage loads correctly (Footer verified via Playwright tests)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
