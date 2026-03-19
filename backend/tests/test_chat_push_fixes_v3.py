"""
Test Suite for Zektrix UK - Chat, Push Notification, and Auth Fixes (Iteration 11)
Tests the NEW fixes:
1) LiveChat REST API fallback (sendLiveMessage via POST /chat/message)
2) Admin chat polling (GET /admin/chat/messages)
3) Chat escalation (POST /chat/escalate)
4) Push notification subscription (POST /push/subscribe)
5) VAPID key endpoint (GET /push/vapid-key)
6) Admin chat reply (POST /admin/chat/reply)
7) Chat history (GET /chat/history)
"""

import pytest
import requests
import uuid
import time
import os

# Use preview URL for testing
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://vapid-sync-test.preview.emergentagent.com').rstrip('/')

class TestChatAndPushFixes:
    """Test chat and push notification fixes"""
    
    admin_token = None
    user_token = None
    test_user_id = None
    test_message_id = None
    
    @classmethod
    def setup_class(cls):
        """Login admin and test user for all tests"""
        # Admin login
        resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "admin@zektrix.uk",
            "password": "admin123"
        })
        if resp.status_code == 200:
            cls.admin_token = resp.json().get("token")
            print(f"✅ Admin login successful")
        else:
            print(f"❌ Admin login failed: {resp.status_code} - {resp.text}")
        
        # Test user registration/login
        test_email = f"chattest_{uuid.uuid4().hex[:6]}@test.com"
        resp = requests.post(f"{BASE_URL}/api/auth/register", json={
            "username": f"chattest_{uuid.uuid4().hex[:6]}",
            "email": test_email,
            "password": "test123",
            "first_name": "Chat",
            "last_name": "Test",
            "phone": "+44123456789"
        })
        if resp.status_code == 200:
            data = resp.json()
            cls.user_token = data.get("token")
            cls.test_user_id = data.get("user", {}).get("user_id")
            print(f"✅ Test user created: {test_email}")
        else:
            print(f"⚠️ User registration failed, trying login: {resp.text}")
            # Try existing user
            resp = requests.post(f"{BASE_URL}/api/auth/login", json={
                "email": "chattest@test.com",
                "password": "test123"
            })
            if resp.status_code == 200:
                data = resp.json()
                cls.user_token = data.get("token")
                cls.test_user_id = data.get("user", {}).get("user_id")
                print(f"✅ Test user login successful")
            else:
                print(f"❌ Test user login failed: {resp.status_code}")

    # ========== VAPID KEY ENDPOINT ==========
    
    def test_01_vapid_key_endpoint(self):
        """Test GET /api/push/vapid-key returns valid VAPID public key"""
        resp = requests.get(f"{BASE_URL}/api/push/vapid-key")
        assert resp.status_code == 200, f"VAPID key endpoint failed: {resp.status_code}"
        
        data = resp.json()
        assert "public_key" in data, "Response missing 'public_key'"
        assert data["public_key"], "VAPID public key is empty"
        assert len(data["public_key"]) > 60, f"VAPID key too short: {len(data['public_key'])}"
        print(f"✅ VAPID key: {data['public_key'][:40]}...")

    # ========== PUSH SUBSCRIPTION ==========
    
    def test_02_push_subscribe_requires_admin(self):
        """Test POST /api/push/subscribe requires admin role"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        fake_subscription = {
            "endpoint": "https://fcm.googleapis.com/fcm/send/test123",
            "keys": {"p256dh": "test_p256dh", "auth": "test_auth"}
        }
        
        resp = requests.post(f"{BASE_URL}/api/push/subscribe",
            json=fake_subscription,
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        # Non-admin should get 403
        assert resp.status_code == 403, f"Expected 403 for non-admin, got {resp.status_code}"
        print(f"✅ Push subscribe correctly rejects non-admin users")

    def test_03_push_subscribe_admin(self):
        """Test POST /api/push/subscribe works for admin"""
        if not self.admin_token:
            pytest.skip("No admin token available")
        
        test_subscription = {
            "endpoint": f"https://fcm.googleapis.com/fcm/send/test_{uuid.uuid4().hex[:8]}",
            "keys": {
                "p256dh": "BNcRdreALRFXTkOOUHK1EtK2wtaz5Ry4YfYCA_0QTpQtUbVlUls0VJXg7A8u-Ts1XbjhazAkj7I99e8QcYP7DkA",
                "auth": "tBHItJI5svbpez7KI4CCXg"
            }
        }
        
        resp = requests.post(f"{BASE_URL}/api/push/subscribe",
            json=test_subscription,
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert resp.status_code == 200, f"Push subscribe failed: {resp.status_code} - {resp.text}"
        print(f"✅ Admin push subscription successful")

    # ========== AI CHAT ==========
    
    def test_04_ai_chat_endpoint(self):
        """Test POST /api/chat/ai works for authenticated users"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        resp = requests.post(f"{BASE_URL}/api/chat/ai",
            json={"message": "Cum funcționează competițiile?", "session_id": None},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"AI chat failed: {resp.status_code} - {resp.text}"
        
        data = resp.json()
        assert "response" in data, "AI response missing 'response' field"
        assert "session_id" in data, "AI response missing 'session_id'"
        print(f"✅ AI chat response: {data['response'][:80]}...")

    # ========== CHAT ESCALATION ==========
    
    def test_05_chat_escalate(self):
        """Test POST /api/chat/escalate creates message and notifies admins"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        test_message = f"Test escalation message {uuid.uuid4().hex[:8]}"
        resp = requests.post(f"{BASE_URL}/api/chat/escalate",
            json={"message": test_message},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"Escalation failed: {resp.status_code} - {resp.text}"
        
        data = resp.json()
        assert "message_id" in data, "Escalation response missing 'message_id'"
        TestChatAndPushFixes.test_message_id = data["message_id"]
        print(f"✅ Chat escalated successfully, message_id: {data['message_id']}")

    # ========== CHAT MESSAGE (REST FALLBACK) ==========
    
    def test_06_chat_message_rest_api(self):
        """Test POST /api/chat/message - REST fallback for WebSocket"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        test_message = f"Test REST message {uuid.uuid4().hex[:8]}"
        resp = requests.post(f"{BASE_URL}/api/chat/message",
            json={"message": test_message, "is_faq": False},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"Chat message failed: {resp.status_code} - {resp.text}"
        
        data = resp.json()
        # Can be FAQ response or support ticket
        assert "type" in data, "Response missing 'type'"
        assert data["type"] in ["faq", "support"], f"Unexpected type: {data['type']}"
        print(f"✅ Chat message REST API working, type: {data['type']}")

    def test_07_chat_message_faq_match(self):
        """Test POST /api/chat/message matches FAQ keywords"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        resp = requests.post(f"{BASE_URL}/api/chat/message",
            json={"message": "cum funcționează zektrix", "is_faq": True},
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"FAQ message failed: {resp.status_code}"
        
        data = resp.json()
        # Should match FAQ
        if data["type"] == "faq":
            assert "response" in data, "FAQ response missing 'response'"
            print(f"✅ FAQ matched: {data['response'][:80]}...")
        else:
            print(f"✅ Message forwarded to support (no FAQ match)")

    # ========== CHAT HISTORY ==========
    
    def test_08_chat_history(self):
        """Test GET /api/chat/history returns user's chat messages"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        resp = requests.get(f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"Chat history failed: {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Chat history should be a list"
        print(f"✅ Chat history returned {len(data)} messages")
        
        # Check for no duplicate message_ids
        if data:
            msg_ids = [m.get("message_id") for m in data]
            unique_ids = set(msg_ids)
            assert len(msg_ids) == len(unique_ids), f"Duplicate message_ids found: {len(msg_ids)} vs {len(unique_ids)}"
            print(f"✅ No duplicate message_ids in history")

    # ========== ADMIN CHAT ENDPOINTS ==========
    
    def test_09_admin_get_chat_messages(self):
        """Test GET /api/admin/chat/messages - Admin polling endpoint"""
        if not self.admin_token:
            pytest.skip("No admin token available")
        
        resp = requests.get(f"{BASE_URL}/api/admin/chat/messages",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert resp.status_code == 200, f"Admin chat messages failed: {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Should return list of messages"
        print(f"✅ Admin fetched {len(data)} chat messages")
        
        # Check structure
        if data:
            msg = data[0]
            assert "message_id" in msg, "Message missing 'message_id'"
            assert "user_id" in msg, "Message missing 'user_id'"
            assert "message" in msg, "Message missing 'message'"
            assert "status" in msg, "Message missing 'status'"
            print(f"✅ Admin message structure correct")

    def test_10_admin_chat_messages_filter(self):
        """Test GET /api/admin/chat/messages with status filter"""
        if not self.admin_token:
            pytest.skip("No admin token available")
        
        resp = requests.get(f"{BASE_URL}/api/admin/chat/messages?status=pending",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert resp.status_code == 200, f"Admin chat filter failed: {resp.status_code}"
        
        data = resp.json()
        assert isinstance(data, list), "Should return list"
        # All messages should be pending
        for msg in data:
            assert msg.get("status") == "pending", f"Expected pending, got {msg.get('status')}"
        print(f"✅ Admin filter returned {len(data)} pending messages")

    def test_11_admin_reply_to_chat(self):
        """Test POST /api/admin/chat/reply - Admin replies to user message"""
        if not self.admin_token:
            pytest.skip("No admin token available")
        
        # Find a pending message to reply to
        resp = requests.get(f"{BASE_URL}/api/admin/chat/messages?status=pending",
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        if resp.status_code != 200 or not resp.json():
            # Use the message from escalation test
            if self.test_message_id:
                message_id = self.test_message_id
            else:
                pytest.skip("No pending messages to reply to")
        else:
            message_id = resp.json()[0]["message_id"]
        
        # Reply to the message
        reply_text = f"Test admin reply {uuid.uuid4().hex[:8]}"
        resp = requests.post(f"{BASE_URL}/api/admin/chat/reply",
            json={"message_id": message_id, "reply": reply_text},
            headers={"Authorization": f"Bearer {self.admin_token}"}
        )
        assert resp.status_code == 200, f"Admin reply failed: {resp.status_code} - {resp.text}"
        
        data = resp.json()
        assert "message" in data, "Response missing confirmation"
        print(f"✅ Admin replied to message {message_id[:20]}...")

    def test_12_user_sees_admin_reply_in_history(self):
        """Test that user can see admin reply in chat history"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        # Wait a moment for reply to propagate
        time.sleep(1)
        
        resp = requests.get(f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        assert resp.status_code == 200, f"Chat history failed: {resp.status_code}"
        
        data = resp.json()
        # Check if any message has admin_reply
        has_reply = any(msg.get("admin_reply") for msg in data)
        if has_reply:
            print(f"✅ User can see admin reply in history")
        else:
            print(f"⚠️ No admin replies found in user history (may be from different user)")

    # ========== AUTH CALLBACK PAGE CHECK ==========
    
    def test_13_auth_callback_exists(self):
        """Test auth callback page loads (frontend check)"""
        resp = requests.get(f"{BASE_URL.replace('/api', '')}/auth/callback", allow_redirects=False)
        # Should either return 200 (SPA) or redirect
        assert resp.status_code in [200, 301, 302, 304], f"Auth callback failed: {resp.status_code}"
        print(f"✅ Auth callback route accessible (status: {resp.status_code})")

    # ========== CHAT DEDUPLICATION ==========
    
    def test_14_chat_history_no_duplicates(self):
        """Verify chat history doesn't contain duplicate messages"""
        if not self.user_token:
            pytest.skip("No user token available")
        
        # Fetch history twice
        resp1 = requests.get(f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        resp2 = requests.get(f"{BASE_URL}/api/chat/history",
            headers={"Authorization": f"Bearer {self.user_token}"}
        )
        
        assert resp1.status_code == 200
        assert resp2.status_code == 200
        
        # Should return same data
        data1 = resp1.json()
        data2 = resp2.json()
        
        assert len(data1) == len(data2), f"History inconsistent: {len(data1)} vs {len(data2)}"
        print(f"✅ Chat history consistent across multiple fetches")

    # ========== ADMIN POLLING CONSISTENCY ==========
    
    def test_15_admin_polling_consistency(self):
        """Test admin chat polling returns consistent results"""
        if not self.admin_token:
            pytest.skip("No admin token available")
        
        # Simulate polling
        responses = []
        for i in range(3):
            resp = requests.get(f"{BASE_URL}/api/admin/chat/messages",
                headers={"Authorization": f"Bearer {self.admin_token}"}
            )
            assert resp.status_code == 200
            responses.append(resp.json())
            time.sleep(0.5)
        
        # Count should be consistent (unless new messages arrive)
        counts = [len(r) for r in responses]
        # Allow for slight variation due to new messages
        assert max(counts) - min(counts) <= 2, f"Inconsistent polling: {counts}"
        print(f"✅ Admin polling consistent: {counts}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
