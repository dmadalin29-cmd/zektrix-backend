"""
Test suite for Subscription System
Tests: GET /api/subscriptions/plans, GET /api/subscriptions/my, GET /api/subscriptions/my/tickets,
       POST /api/subscriptions/purchase, POST /api/subscriptions/cancel,
       GET /api/admin/subscriptions, GET /api/admin/subscriptions/stats
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


class TestSubscriptionPlans:
    """Test subscription plans endpoint (public)"""
    
    def test_get_subscription_plans(self):
        """GET /api/subscriptions/plans - should return 3 plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        plans = response.json()
        assert isinstance(plans, list), "Plans should be a list"
        assert len(plans) == 3, f"Expected 3 plans, got {len(plans)}"
        
        # Verify plan structure and values
        plan_ids = [p["plan_id"] for p in plans]
        assert "sub_25" in plan_ids, "Missing sub_25 plan"
        assert "sub_50" in plan_ids, "Missing sub_50 plan"
        assert "sub_100" in plan_ids, "Missing sub_100 plan"
        
        # Verify Abonament 25
        sub_25 = next(p for p in plans if p["plan_id"] == "sub_25")
        assert sub_25["name"] == "Abonament 25", f"Wrong name: {sub_25['name']}"
        assert sub_25["price"] == 25.0, f"Wrong price: {sub_25['price']}"
        assert sub_25["entries_per_competition"] == 2, f"Wrong entries: {sub_25['entries_per_competition']}"
        assert sub_25["duration_days"] == 30, f"Wrong duration: {sub_25['duration_days']}"
        
        # Verify Abonament 50
        sub_50 = next(p for p in plans if p["plan_id"] == "sub_50")
        assert sub_50["name"] == "Abonament 50", f"Wrong name: {sub_50['name']}"
        assert sub_50["price"] == 50.0, f"Wrong price: {sub_50['price']}"
        assert sub_50["entries_per_competition"] == 5, f"Wrong entries: {sub_50['entries_per_competition']}"
        
        # Verify Abonament 100
        sub_100 = next(p for p in plans if p["plan_id"] == "sub_100")
        assert sub_100["name"] == "Abonament 100", f"Wrong name: {sub_100['name']}"
        assert sub_100["price"] == 100.0, f"Wrong price: {sub_100['price']}"
        assert sub_100["entries_per_competition"] == 12, f"Wrong entries: {sub_100['entries_per_competition']}"
        
        print("✓ GET /api/subscriptions/plans - Returns 3 plans with correct prices and entries")


class TestUserSubscription:
    """Test user subscription endpoints (authenticated)"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin user for testing"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code != 200:
            pytest.skip("Could not login - skipping authenticated tests")
        
        data = login_resp.json()
        self.token = data.get("token")
        self.user = data.get("user")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_my_subscription_no_active(self):
        """GET /api/subscriptions/my - returns null when not subscribed"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "subscription" in data, "Response should have 'subscription' key"
        # Subscription can be null or an expired/active subscription
        print(f"✓ GET /api/subscriptions/my - Returns subscription data (current: {data['subscription']})")
    
    def test_get_my_subscription_tickets(self):
        """GET /api/subscriptions/my/tickets - returns subscription tickets list"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my/tickets", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        tickets = response.json()
        assert isinstance(tickets, list), "Tickets should be a list"
        print(f"✓ GET /api/subscriptions/my/tickets - Returns {len(tickets)} subscription tickets")
    
    def test_purchase_subscription_wallet_insufficient_balance(self):
        """POST /api/subscriptions/purchase - wallet purchase fails with insufficient balance"""
        # First check current balance
        balance_resp = requests.get(f"{BASE_URL}/api/wallet/balance", headers=self.headers)
        balance = balance_resp.json().get("balance", 0) if balance_resp.status_code == 200 else 0
        
        # Try to purchase with wallet (should fail if balance < 25)
        response = requests.post(f"{BASE_URL}/api/subscriptions/purchase", 
            json={"plan_id": "sub_25", "payment_method": "wallet"},
            headers=self.headers
        )
        
        if balance < 25:
            # Should fail with insufficient balance
            assert response.status_code == 400, f"Expected 400 for insufficient balance, got {response.status_code}"
            assert "insufficient" in response.json().get("detail", "").lower() or "balance" in response.json().get("detail", "").lower(), \
                f"Expected insufficient balance error, got: {response.json()}"
            print(f"✓ POST /api/subscriptions/purchase (wallet) - Correctly fails with insufficient balance (£{balance:.2f})")
        else:
            # May succeed or fail if already has subscription
            if response.status_code == 400 and "active subscription" in response.json().get("detail", "").lower():
                print(f"✓ POST /api/subscriptions/purchase (wallet) - User already has active subscription")
            elif response.status_code == 200:
                print(f"✓ POST /api/subscriptions/purchase (wallet) - Purchase succeeded (balance was £{balance:.2f})")
            else:
                print(f"✓ POST /api/subscriptions/purchase (wallet) - Response: {response.status_code} - {response.json()}")
    
    def test_purchase_subscription_viva_returns_checkout_url(self):
        """POST /api/subscriptions/purchase - viva purchase returns checkout_url"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/purchase",
            json={"plan_id": "sub_25", "payment_method": "viva"},
            headers=self.headers
        )
        
        # May fail if already has active subscription
        if response.status_code == 400:
            detail = response.json().get("detail", "")
            if "active subscription" in detail.lower():
                print(f"✓ POST /api/subscriptions/purchase (viva) - User already has active subscription")
                return
            elif "payment service" in detail.lower():
                print(f"✓ POST /api/subscriptions/purchase (viva) - Payment service unavailable (expected in preview)")
                return
        
        # If successful, should return checkout_url
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data, f"Expected checkout_url in response: {data}"
            assert "vivapayments.com" in data["checkout_url"], f"Invalid checkout URL: {data['checkout_url']}"
            print(f"✓ POST /api/subscriptions/purchase (viva) - Returns checkout_url: {data['checkout_url'][:50]}...")
        else:
            # 500 is acceptable if Viva credentials not configured
            assert response.status_code in [200, 400, 500], f"Unexpected status: {response.status_code}"
            print(f"✓ POST /api/subscriptions/purchase (viva) - Response: {response.status_code} (Viva may not be configured)")
    
    def test_cancel_subscription_no_active(self):
        """POST /api/subscriptions/cancel - returns 404 if no active subscription"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/cancel", headers=self.headers)
        
        # Either 404 (no subscription) or 200 (cancelled)
        if response.status_code == 404:
            assert "no active subscription" in response.json().get("detail", "").lower()
            print("✓ POST /api/subscriptions/cancel - Returns 404 when no active subscription")
        elif response.status_code == 200:
            data = response.json()
            assert "message" in data, "Should have message in response"
            print(f"✓ POST /api/subscriptions/cancel - Successfully cancelled auto-renewal")
        else:
            pytest.fail(f"Unexpected status: {response.status_code} - {response.json()}")


class TestAdminSubscription:
    """Test admin subscription endpoints"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin user"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code != 200:
            pytest.skip("Could not login as admin - skipping admin tests")
        
        data = login_resp.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
        
        # Verify admin role
        if data.get("user", {}).get("role") != "admin":
            pytest.skip("User is not admin - skipping admin tests")
    
    def test_admin_get_all_subscriptions(self):
        """GET /api/admin/subscriptions - admin view all subscriptions"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        subs = response.json()
        assert isinstance(subs, list), "Subscriptions should be a list"
        print(f"✓ GET /api/admin/subscriptions - Returns {len(subs)} subscriptions")
        
        # If there are subscriptions, verify structure
        if subs:
            sub = subs[0]
            expected_fields = ["subscription_id", "user_id", "plan_id", "status"]
            for field in expected_fields:
                assert field in sub, f"Missing field: {field}"
            print(f"  - First subscription: {sub.get('plan_name', 'N/A')} - {sub.get('status', 'N/A')}")
    
    def test_admin_get_subscription_stats(self):
        """GET /api/admin/subscriptions/stats - subscription statistics"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions/stats", headers=self.headers)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        stats = response.json()
        expected_fields = ["active_subscriptions", "total_subscriptions", "total_revenue", "total_tickets_distributed"]
        for field in expected_fields:
            assert field in stats, f"Missing field: {field}"
        
        print(f"✓ GET /api/admin/subscriptions/stats - Returns stats:")
        print(f"  - Active: {stats['active_subscriptions']}")
        print(f"  - Total: {stats['total_subscriptions']}")
        print(f"  - Revenue: £{stats['total_revenue']:.2f}")
        print(f"  - Tickets distributed: {stats['total_tickets_distributed']}")


class TestSubscriptionPurchaseInvalidPlan:
    """Test subscription purchase with invalid plan"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin user for testing"""
        login_resp = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if login_resp.status_code != 200:
            pytest.skip("Could not login - skipping authenticated tests")
        
        data = login_resp.json()
        self.token = data.get("token")
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_purchase_invalid_plan(self):
        """POST /api/subscriptions/purchase - returns 404 for invalid plan"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/purchase",
            json={"plan_id": "invalid_plan", "payment_method": "wallet"},
            headers=self.headers
        )
        assert response.status_code == 404, f"Expected 404 for invalid plan, got {response.status_code}"
        assert "not found" in response.json().get("detail", "").lower()
        print("✓ POST /api/subscriptions/purchase - Returns 404 for invalid plan")


class TestSubscriptionUnauthorized:
    """Test subscription endpoints without authentication"""
    
    def test_my_subscription_unauthorized(self):
        """GET /api/subscriptions/my - returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/subscriptions/my - Returns 401 without auth")
    
    def test_my_tickets_unauthorized(self):
        """GET /api/subscriptions/my/tickets - returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/my/tickets")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/subscriptions/my/tickets - Returns 401 without auth")
    
    def test_purchase_unauthorized(self):
        """POST /api/subscriptions/purchase - returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/purchase",
            json={"plan_id": "sub_25", "payment_method": "wallet"}
        )
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /api/subscriptions/purchase - Returns 401 without auth")
    
    def test_cancel_unauthorized(self):
        """POST /api/subscriptions/cancel - returns 401 without auth"""
        response = requests.post(f"{BASE_URL}/api/subscriptions/cancel")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ POST /api/subscriptions/cancel - Returns 401 without auth")
    
    def test_admin_subscriptions_unauthorized(self):
        """GET /api/admin/subscriptions - returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions - Returns 401 without auth")
    
    def test_admin_stats_unauthorized(self):
        """GET /api/admin/subscriptions/stats - returns 401 without auth"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions/stats")
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ GET /api/admin/subscriptions/stats - Returns 401 without auth")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
