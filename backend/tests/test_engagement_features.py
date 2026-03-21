"""
Test suite for 5 Engagement Features:
1. Loyalty Points - GET /api/loyalty/my, POST /api/loyalty/redeem
2. User In-App Notifications - GET /api/notifications/my, POST /api/notifications/read-all
3. Reviews/Testimonials - GET /api/reviews, GET /api/reviews/pending, POST /api/reviews/{id}/approve
4. Wheel of Fortune - GET /api/wheel/prizes, GET /api/wheel/status, POST /api/wheel/spin
5. Exit Intent Popup - POST /api/exit-intent/claim, GET /api/discounts/my
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


@pytest.fixture(scope="module")
def admin_token():
    """Get admin authentication token"""
    response = requests.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin login failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


# ==================== LOYALTY POINTS TESTS ====================

class TestLoyaltyPoints:
    """Tests for Loyalty Points feature"""
    
    def test_get_loyalty_info_requires_auth(self, api_client):
        """GET /api/loyalty/my should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/loyalty/my")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/loyalty/my requires auth")
    
    def test_get_loyalty_info_authenticated(self, api_client, admin_token):
        """GET /api/loyalty/my should return loyalty info for authenticated user"""
        response = api_client.get(
            f"{BASE_URL}/api/loyalty/my",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        # Verify response structure
        assert "points" in data, "Response should contain 'points'"
        assert "total_earned" in data, "Response should contain 'total_earned'"
        assert "redeemable_value" in data, "Response should contain 'redeemable_value'"
        assert "tier" in data, "Response should contain 'tier'"
        assert "points_per_pound" in data, "Response should contain 'points_per_pound'"
        assert "redeem_rate" in data, "Response should contain 'redeem_rate'"
        
        # Verify tier structure
        tier = data["tier"]
        assert "name" in tier, "Tier should have 'name'"
        assert "color" in tier, "Tier should have 'color'"
        assert "bonus_multiplier" in tier, "Tier should have 'bonus_multiplier'"
        
        print(f"PASS: GET /api/loyalty/my returns: points={data['points']}, tier={tier['name']}, redeemable=£{data['redeemable_value']}")
    
    def test_redeem_loyalty_points_requires_auth(self, api_client):
        """POST /api/loyalty/redeem should require authentication"""
        response = api_client.post(f"{BASE_URL}/api/loyalty/redeem", json={"points": 100})
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/loyalty/redeem requires auth")
    
    def test_redeem_loyalty_points_insufficient(self, api_client, admin_token):
        """POST /api/loyalty/redeem should fail with insufficient points"""
        # First check current points
        loyalty_response = api_client.get(
            f"{BASE_URL}/api/loyalty/my",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        current_points = loyalty_response.json().get("points", 0)
        
        # Try to redeem more than available
        response = api_client.post(
            f"{BASE_URL}/api/loyalty/redeem",
            json={"points": current_points + 1000},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        print(f"PASS: POST /api/loyalty/redeem fails with insufficient points (current: {current_points})")
    
    def test_redeem_loyalty_points_invalid_amount(self, api_client, admin_token):
        """POST /api/loyalty/redeem should fail with non-multiple of 100"""
        response = api_client.post(
            f"{BASE_URL}/api/loyalty/redeem",
            json={"points": 150},  # Not a multiple of 100
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        # Should fail either due to validation or insufficient points
        assert response.status_code in [400, 422], f"Expected 400/422, got {response.status_code}"
        print("PASS: POST /api/loyalty/redeem validates point amounts")


# ==================== NOTIFICATIONS TESTS ====================

class TestUserNotifications:
    """Tests for User In-App Notifications feature"""
    
    def test_get_notifications_requires_auth(self, api_client):
        """GET /api/notifications/my should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/notifications/my")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/notifications/my requires auth")
    
    def test_get_notifications_authenticated(self, api_client, admin_token):
        """GET /api/notifications/my should return notifications for authenticated user"""
        response = api_client.get(
            f"{BASE_URL}/api/notifications/my",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "notifications" in data, "Response should contain 'notifications'"
        assert "unread_count" in data, "Response should contain 'unread_count'"
        assert isinstance(data["notifications"], list), "notifications should be a list"
        assert isinstance(data["unread_count"], int), "unread_count should be an integer"
        
        print(f"PASS: GET /api/notifications/my returns {len(data['notifications'])} notifications, {data['unread_count']} unread")
    
    def test_mark_all_notifications_read_requires_auth(self, api_client):
        """POST /api/notifications/read-all should require authentication"""
        response = api_client.post(f"{BASE_URL}/api/notifications/read-all")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/notifications/read-all requires auth")
    
    def test_mark_all_notifications_read(self, api_client, admin_token):
        """POST /api/notifications/read-all should mark all notifications as read"""
        response = api_client.post(
            f"{BASE_URL}/api/notifications/read-all",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        
        # Verify unread count is now 0
        verify_response = api_client.get(
            f"{BASE_URL}/api/notifications/my",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        verify_data = verify_response.json()
        assert verify_data["unread_count"] == 0, f"Expected 0 unread, got {verify_data['unread_count']}"
        
        print("PASS: POST /api/notifications/read-all marks all as read")


# ==================== REVIEWS TESTS ====================

class TestReviews:
    """Tests for Reviews/Testimonials feature"""
    
    def test_get_public_reviews(self, api_client):
        """GET /api/reviews should return approved reviews (public endpoint)"""
        response = api_client.get(f"{BASE_URL}/api/reviews")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # If there are reviews, verify structure
        if len(data) > 0:
            review = data[0]
            assert "review_id" in review, "Review should have 'review_id'"
            assert "username" in review, "Review should have 'username'"
            assert "rating" in review, "Review should have 'rating'"
            assert "text" in review, "Review should have 'text'"
            # All returned reviews should be approved
            assert review.get("approved") == True, "Public reviews should be approved"
        
        print(f"PASS: GET /api/reviews returns {len(data)} approved reviews")
    
    def test_get_pending_reviews_requires_admin(self, api_client):
        """GET /api/reviews/pending should require admin authentication"""
        response = api_client.get(f"{BASE_URL}/api/reviews/pending")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/reviews/pending requires admin auth")
    
    def test_get_pending_reviews_admin(self, api_client, admin_token):
        """GET /api/reviews/pending should return pending reviews for admin"""
        response = api_client.get(
            f"{BASE_URL}/api/reviews/pending",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # All returned reviews should be pending (not approved)
        for review in data:
            assert review.get("approved") == False, "Pending reviews should not be approved"
        
        print(f"PASS: GET /api/reviews/pending returns {len(data)} pending reviews")
    
    def test_approve_review_requires_admin(self, api_client):
        """POST /api/reviews/{id}/approve should require admin authentication"""
        response = api_client.post(f"{BASE_URL}/api/reviews/fake_id/approve")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/reviews/{id}/approve requires admin auth")


# ==================== WHEEL OF FORTUNE TESTS ====================

class TestWheelOfFortune:
    """Tests for Wheel of Fortune feature"""
    
    def test_get_wheel_prizes_public(self, api_client):
        """GET /api/wheel/prizes should return 8 wheel prizes (public endpoint)"""
        response = api_client.get(f"{BASE_URL}/api/wheel/prizes")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        assert len(data) == 8, f"Expected 8 prizes, got {len(data)}"
        
        # Verify prize structure (should NOT include probability)
        for prize in data:
            assert "id" in prize, "Prize should have 'id'"
            assert "label" in prize, "Prize should have 'label'"
            assert "color" in prize, "Prize should have 'color'"
            assert "probability" not in prize, "Prize should NOT expose probability"
        
        print(f"PASS: GET /api/wheel/prizes returns 8 prizes: {[p['label'] for p in data]}")
    
    def test_get_wheel_status_requires_auth(self, api_client):
        """GET /api/wheel/status should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/wheel/status")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/wheel/status requires auth")
    
    def test_get_wheel_status_authenticated(self, api_client, admin_token):
        """GET /api/wheel/status should return spin status for authenticated user"""
        response = api_client.get(
            f"{BASE_URL}/api/wheel/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "can_spin" in data, "Response should contain 'can_spin'"
        assert isinstance(data["can_spin"], bool), "can_spin should be boolean"
        
        # If user already spun, previous_spin should be present
        if not data["can_spin"]:
            assert "previous_spin" in data, "If can_spin=false, previous_spin should be present"
            if data["previous_spin"]:
                assert "prize_label" in data["previous_spin"], "previous_spin should have prize_label"
        
        print(f"PASS: GET /api/wheel/status returns can_spin={data['can_spin']}")
    
    def test_spin_wheel_requires_auth(self, api_client):
        """POST /api/wheel/spin should require authentication"""
        response = api_client.post(f"{BASE_URL}/api/wheel/spin")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/wheel/spin requires auth")
    
    def test_spin_wheel_once_per_user(self, api_client, admin_token):
        """POST /api/wheel/spin should only allow one spin per user"""
        # First check if user can spin
        status_response = api_client.get(
            f"{BASE_URL}/api/wheel/status",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        status_data = status_response.json()
        
        if status_data["can_spin"]:
            # User hasn't spun yet - spin the wheel
            spin_response = api_client.post(
                f"{BASE_URL}/api/wheel/spin",
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert spin_response.status_code == 200, f"Expected 200, got {spin_response.status_code}: {spin_response.text}"
            
            spin_data = spin_response.json()
            assert "prize_id" in spin_data, "Spin response should have prize_id"
            assert "prize_label" in spin_data, "Spin response should have prize_label"
            assert "prize_type" in spin_data, "Spin response should have prize_type"
            
            print(f"PASS: POST /api/wheel/spin - Won: {spin_data['prize_label']} (type: {spin_data['prize_type']})")
            
            # Try to spin again - should fail
            second_spin = api_client.post(
                f"{BASE_URL}/api/wheel/spin",
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert second_spin.status_code == 400, f"Second spin should fail with 400, got {second_spin.status_code}"
            print("PASS: Second spin correctly rejected")
        else:
            # User already spun - verify spin fails
            spin_response = api_client.post(
                f"{BASE_URL}/api/wheel/spin",
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert spin_response.status_code == 400, f"Expected 400 (already spun), got {spin_response.status_code}"
            print(f"PASS: POST /api/wheel/spin correctly rejects (user already spun, won: {status_data.get('previous_spin', {}).get('prize_label', 'unknown')})")


# ==================== EXIT INTENT DISCOUNT TESTS ====================

class TestExitIntentDiscount:
    """Tests for Exit Intent Discount feature"""
    
    def test_claim_exit_discount_requires_auth(self, api_client):
        """POST /api/exit-intent/claim should require authentication"""
        response = api_client.post(f"{BASE_URL}/api/exit-intent/claim")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: POST /api/exit-intent/claim requires auth")
    
    def test_claim_exit_discount_once_per_user(self, api_client, admin_token):
        """POST /api/exit-intent/claim should only allow one claim per user"""
        response = api_client.post(
            f"{BASE_URL}/api/exit-intent/claim",
            json={},
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        
        # Either success (first claim) or 400 (already claimed)
        if response.status_code == 200:
            data = response.json()
            assert data.get("success") == True, "Response should indicate success"
            assert data.get("discount_percent") == 15, "Discount should be 15%"
            assert "expires_at" in data, "Response should have expires_at"
            print(f"PASS: POST /api/exit-intent/claim - 15% discount claimed, expires: {data['expires_at']}")
            
            # Try to claim again - should fail
            second_claim = api_client.post(
                f"{BASE_URL}/api/exit-intent/claim",
                json={},
                headers={"Authorization": f"Bearer {admin_token}"}
            )
            assert second_claim.status_code == 400, f"Second claim should fail with 400, got {second_claim.status_code}"
            print("PASS: Second claim correctly rejected")
        else:
            assert response.status_code == 400, f"Expected 400 (already claimed), got {response.status_code}"
            print("PASS: POST /api/exit-intent/claim correctly rejects (user already claimed)")
    
    def test_get_my_discounts_requires_auth(self, api_client):
        """GET /api/discounts/my should require authentication"""
        response = api_client.get(f"{BASE_URL}/api/discounts/my")
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("PASS: GET /api/discounts/my requires auth")
    
    def test_get_my_discounts_authenticated(self, api_client, admin_token):
        """GET /api/discounts/my should return active discounts for authenticated user"""
        response = api_client.get(
            f"{BASE_URL}/api/discounts/my",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify discount structure if any exist
        for discount in data:
            assert "discount_id" in discount, "Discount should have 'discount_id'"
            assert "percent" in discount, "Discount should have 'percent'"
            assert "expires_at" in discount, "Discount should have 'expires_at'"
            assert "source" in discount, "Discount should have 'source'"
            assert discount.get("used") == False, "Active discounts should not be used"
        
        print(f"PASS: GET /api/discounts/my returns {len(data)} active discounts")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
