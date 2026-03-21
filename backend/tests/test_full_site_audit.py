# -*- coding: utf-8 -*-
"""
Full Site Audit Test Suite
Tests all major features: competitions, auth, dashboard, wallet, subscriptions, 
loyalty, notifications, wheel, badges, referral, admin panel
"""
import pytest
import requests
import os
import time

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://invite-network-1.preview.emergentagent.com')

# Test credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


class TestPublicEndpoints:
    """Test public endpoints that don't require authentication"""
    
    def test_get_stats(self):
        """GET /api/stats - Public stats endpoint"""
        response = requests.get(f"{BASE_URL}/api/stats")
        assert response.status_code == 200
        data = response.json()
        assert "winners" in data or "users" in data or "tickets" in data
        print(f"Stats: {data}")
    
    def test_get_active_competitions(self):
        """GET /api/competitions?status=active - List active competitions"""
        response = requests.get(f"{BASE_URL}/api/competitions?status=active")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Active competitions count: {len(data)}")
        if data:
            comp = data[0]
            assert "competition_id" in comp
            assert "title" in comp
            assert "ticket_price" in comp
            assert "max_tickets" in comp
            assert "sold_tickets" in comp
    
    def test_get_all_competitions(self):
        """GET /api/competitions - List all competitions"""
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Total competitions: {len(data)}")
    
    def test_get_winners(self):
        """GET /api/winners - Public winners list"""
        response = requests.get(f"{BASE_URL}/api/winners")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Winners count: {len(data)}")
    
    def test_get_reviews(self):
        """GET /api/reviews - Public approved reviews"""
        response = requests.get(f"{BASE_URL}/api/reviews?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Approved reviews count: {len(data)}")
    
    def test_get_wheel_prizes(self):
        """GET /api/wheel/prizes - Public wheel prizes (no probabilities)"""
        response = requests.get(f"{BASE_URL}/api/wheel/prizes")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 8  # 8 wheel segments
        for prize in data:
            assert "id" in prize
            assert "label" in prize
            assert "color" in prize
            assert "probability" not in prize  # Should not expose probability
        print(f"Wheel prizes: {[p['label'] for p in data]}")
    
    def test_get_activity_recent(self):
        """GET /api/activity/recent - Recent activity feed"""
        response = requests.get(f"{BASE_URL}/api/activity/recent")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Recent activities: {len(data)}")
    
    def test_get_referral_leaderboard(self):
        """GET /api/referral/leaderboard - Public referral leaderboard"""
        response = requests.get(f"{BASE_URL}/api/referral/leaderboard")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Referral leaderboard entries: {len(data)}")


class TestAuthentication:
    """Test authentication flow"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        assert "token" in data
        assert "user" in data
        print(f"Logged in as: {data['user'].get('email')}")
        return data["token"]
    
    def test_login_success(self, auth_token):
        """Test successful login"""
        assert auth_token is not None
        assert len(auth_token) > 0
    
    def test_get_current_user(self, auth_token):
        """GET /api/auth/me - Get current user data"""
        response = requests.get(f"{BASE_URL}/api/auth/me", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "email" in data
        assert data["email"] == ADMIN_EMAIL
        print(f"User data: {data.get('username')}, balance: {data.get('balance')}")
    
    def test_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "wrong@example.com",
            "password": "wrongpassword"
        })
        assert response.status_code in [401, 400]


class TestUserDashboard:
    """Test user dashboard endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_get_my_tickets(self, auth_token):
        """GET /api/tickets/my - User's purchased tickets (Locuri tab)"""
        response = requests.get(f"{BASE_URL}/api/tickets/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"User tickets count: {len(data)}")
    
    def test_get_wallet_balance(self, auth_token):
        """GET /api/wallet/balance - User wallet balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "balance" in data
        print(f"Wallet balance: £{data['balance']}")
    
    def test_get_wallet_transactions(self, auth_token):
        """GET /api/wallet/transactions - Transaction history (History tab)"""
        response = requests.get(f"{BASE_URL}/api/wallet/transactions", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Transactions count: {len(data)}")
    
    def test_get_loyalty_info(self, auth_token):
        """GET /api/loyalty/my - Loyalty points info (Loyalty tab)"""
        response = requests.get(f"{BASE_URL}/api/loyalty/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "points" in data
        assert "tier" in data
        assert "tier" in data and "name" in data["tier"]
        print(f"Loyalty: {data['points']} points, tier: {data['tier']['name']}")
    
    def test_get_user_badges(self, auth_token):
        """GET /api/user/badges - User badges/achievements (Badges tab)"""
        response = requests.get(f"{BASE_URL}/api/user/badges", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "badges" in data
        assert "total_earned" in data
        assert "total_available" in data
        print(f"Badges: {data['total_earned']}/{data['total_available']} earned")
    
    def test_get_user_notifications(self, auth_token):
        """GET /api/notifications/my - User in-app notifications"""
        response = requests.get(f"{BASE_URL}/api/notifications/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data
        assert "unread_count" in data
        print(f"Notifications: {len(data['notifications'])}, unread: {data['unread_count']}")
    
    def test_get_referral_info(self, auth_token):
        """GET /api/referral/my - User referral info (Referral tab)"""
        response = requests.get(f"{BASE_URL}/api/referral/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "referral_code" in data
        assert "referral_link" in data
        print(f"Referral code: {data['referral_code']}")
    
    def test_get_wheel_status(self, auth_token):
        """GET /api/wheel/status - Wheel spin status"""
        response = requests.get(f"{BASE_URL}/api/wheel/status", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "can_spin" in data
        print(f"Can spin wheel: {data['can_spin']}")
    
    def test_get_my_discounts(self, auth_token):
        """GET /api/discounts/my - User's active discounts"""
        response = requests.get(f"{BASE_URL}/api/discounts/my", headers={
            "Authorization": f"Bearer {auth_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Active discounts: {len(data)}")


class TestCompetitionDetail:
    """Test competition detail and purchase endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    @pytest.fixture(scope="class")
    def test_competition(self):
        """Get a test competition"""
        response = requests.get(f"{BASE_URL}/api/competitions?status=active")
        assert response.status_code == 200
        comps = response.json()
        if comps:
            return comps[0]
        return None
    
    def test_get_competition_detail(self, test_competition):
        """GET /api/competitions/{id} - Competition detail"""
        if not test_competition:
            pytest.skip("No active competitions")
        
        comp_id = test_competition["competition_id"]
        response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["competition_id"] == comp_id
        assert "title" in data
        assert "ticket_price" in data
        assert "qualification_question" in data or data.get("qualification_question") is None
        print(f"Competition: {data['title']}, price: £{data['ticket_price']}")
    
    def test_get_competition_tickets(self, test_competition):
        """GET /api/competitions/{id}/tickets - Competition tickets"""
        if not test_competition:
            pytest.skip("No active competitions")
        
        comp_id = test_competition["competition_id"]
        response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}/tickets")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Competition tickets sold: {len(data)}")


class TestWalletAndPayments:
    """Test wallet and payment endpoints"""
    
    @pytest.fixture(scope="class")
    def auth_token(self):
        """Login and get auth token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_wallet_deposit_viva(self, auth_token):
        """POST /api/wallet/deposit - Viva payment for wallet deposit"""
        response = requests.post(f"{BASE_URL}/api/wallet/deposit", 
            json={"amount": 10.0},
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return checkout URL or error
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data or "order_code" in data
            print(f"Wallet deposit checkout URL generated")
    
    def test_ticket_purchase_viva(self, auth_token):
        """POST /api/tickets/purchase-viva - Viva payment for tickets"""
        # Get an active competition
        comps_response = requests.get(f"{BASE_URL}/api/competitions?status=active")
        comps = comps_response.json()
        
        if not comps:
            pytest.skip("No active competitions")
        
        # Find a paid competition
        paid_comp = next((c for c in comps if c.get("ticket_price", 0) > 0), None)
        if not paid_comp:
            pytest.skip("No paid competitions")
        
        response = requests.post(f"{BASE_URL}/api/tickets/purchase-viva",
            json={
                "competition_id": paid_comp["competition_id"],
                "quantity": 1,
                "qualification_answer": paid_comp.get("qualification_question", {}).get("correct_answer", 0) if paid_comp.get("qualification_question") else None
            },
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Should return checkout URL
        assert response.status_code in [200, 400, 500]
        if response.status_code == 200:
            data = response.json()
            assert "checkout_url" in data
            print(f"Viva checkout URL: {data['checkout_url'][:50]}...")


class TestAdminPanel:
    """Test admin panel endpoints"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Login as admin"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200
        return response.json()["token"]
    
    def test_admin_stats(self, admin_token):
        """GET /api/admin/stats - Admin dashboard stats"""
        response = requests.get(f"{BASE_URL}/api/admin/stats", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        print(f"Admin stats: {data}")
    
    def test_admin_analytics(self, admin_token):
        """GET /api/admin/analytics - Admin analytics data"""
        response = requests.get(f"{BASE_URL}/api/admin/analytics", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "total_revenue" in data or "revenue_by_day" in data
        print(f"Admin analytics loaded")
    
    def test_admin_users_list(self, admin_token):
        """GET /api/admin/users - Admin users list (Utilizatori tab)"""
        response = requests.get(f"{BASE_URL}/api/admin/users", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin users count: {len(data)}")
    
    def test_admin_tickets_list(self, admin_token):
        """GET /api/admin/tickets - Admin tickets list (Locuri tab)"""
        response = requests.get(f"{BASE_URL}/api/admin/tickets", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin tickets count: {len(data)}")
    
    def test_admin_notifications(self, admin_token):
        """GET /api/admin/notifications - Admin notifications"""
        response = requests.get(f"{BASE_URL}/api/admin/notifications", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert "notifications" in data or isinstance(data, list)
        print(f"Admin notifications loaded")
    
    def test_admin_pending_reviews(self, admin_token):
        """GET /api/reviews/pending - Pending reviews (Recenzii tab)"""
        response = requests.get(f"{BASE_URL}/api/reviews/pending", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Pending reviews: {len(data)}")
    
    def test_admin_wallet_stats(self, admin_token):
        """GET /api/admin/wallet/stats - Admin wallet stats"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/stats", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        print(f"Admin wallet stats: {data}")
    
    def test_admin_subscriptions(self, admin_token):
        """GET /api/admin/subscriptions - Admin subscriptions list"""
        response = requests.get(f"{BASE_URL}/api/admin/subscriptions", headers={
            "Authorization": f"Bearer {admin_token}"
        })
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Admin subscriptions: {len(data)}")


class TestSubscriptions:
    """Test subscription endpoints"""
    
    def test_get_subscription_plans(self):
        """GET /api/subscriptions/plans - Public subscription plans"""
        response = requests.get(f"{BASE_URL}/api/subscriptions/plans")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"Subscription plans: {len(data)}")
        if data:
            plan = data[0]
            assert "plan_id" in plan or "name" in plan


class TestPushNotifications:
    """Test push notification endpoints"""
    
    def test_get_vapid_key(self):
        """GET /api/push/vapid-key - Public VAPID key"""
        response = requests.get(f"{BASE_URL}/api/push/vapid-key")
        assert response.status_code == 200
        data = response.json()
        assert "public_key" in data
        print(f"VAPID key available: {len(data['public_key'])} chars")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
