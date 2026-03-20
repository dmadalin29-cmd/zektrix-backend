"""
Wallet System Tests for Zektrix UK Competition Platform
Tests: wallet balance, deposit, withdraw, transactions, admin wallet management, bonus settings
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


class TestWalletUserEndpoints:
    """User wallet endpoints tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_get_wallet_balance(self):
        """GET /api/wallet/balance - returns user balance"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "balance" in data, "Response should contain 'balance' field"
        assert isinstance(data["balance"], (int, float)), "Balance should be a number"
        print(f"✓ Wallet balance: £{data['balance']:.2f}")
    
    def test_get_wallet_transactions(self):
        """GET /api/wallet/transactions - returns transaction history"""
        response = requests.get(f"{BASE_URL}/api/wallet/transactions", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        if len(data) > 0:
            txn = data[0]
            assert "transaction_id" in txn, "Transaction should have transaction_id"
            assert "transaction_type" in txn, "Transaction should have transaction_type"
            assert "amount" in txn, "Transaction should have amount"
            assert "status" in txn, "Transaction should have status"
            print(f"✓ Found {len(data)} transactions")
        else:
            print("✓ No transactions yet (empty list returned)")
    
    def test_wallet_deposit_creates_checkout_url(self):
        """POST /api/wallet/deposit - creates Viva checkout for deposit"""
        response = requests.post(f"{BASE_URL}/api/wallet/deposit", 
            json={"amount": 10.0},
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "checkout_url" in data, "Response should contain checkout_url"
        assert "order_code" in data, "Response should contain order_code"
        assert "transaction_id" in data, "Response should contain transaction_id"
        assert "amount" in data, "Response should contain amount"
        assert data["amount"] == 10.0, "Amount should match request"
        assert "vivapayments.com" in data["checkout_url"], "Checkout URL should be Viva Payments"
        print(f"✓ Deposit checkout URL created: {data['checkout_url'][:60]}...")
    
    def test_wallet_deposit_minimum_validation(self):
        """POST /api/wallet/deposit - validates minimum £5"""
        response = requests.post(f"{BASE_URL}/api/wallet/deposit", 
            json={"amount": 2.0},
            headers=self.headers
        )
        assert response.status_code == 400, f"Should reject amount below minimum: {response.text}"
        assert "Minimum" in response.json().get("detail", ""), "Error should mention minimum"
        print("✓ Minimum deposit validation works")
    
    def test_wallet_deposit_maximum_validation(self):
        """POST /api/wallet/deposit - validates maximum £5,000"""
        response = requests.post(f"{BASE_URL}/api/wallet/deposit", 
            json={"amount": 6000.0},
            headers=self.headers
        )
        assert response.status_code == 400, f"Should reject amount above maximum: {response.text}"
        assert "Maximum" in response.json().get("detail", ""), "Error should mention maximum"
        print("✓ Maximum deposit validation works")
    
    def test_get_user_withdrawals(self):
        """GET /api/wallet/withdrawals - user's withdrawal history"""
        response = requests.get(f"{BASE_URL}/api/wallet/withdrawals", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Found {len(data)} withdrawal requests")
    
    def test_get_bonus_info_public(self):
        """GET /api/wallet/bonus-info - public bonus info endpoint"""
        # This endpoint is public, no auth needed
        response = requests.get(f"{BASE_URL}/api/wallet/bonus-info")
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "active" in data, "Response should contain 'active' field"
        assert "bonus_percent" in data, "Response should contain 'bonus_percent' field"
        assert "bonus_max" in data, "Response should contain 'bonus_max' field"
        print(f"✓ Bonus info: active={data['active']}, {data['bonus_percent']}% (max £{data['bonus_max']})")


class TestWalletWithdrawal:
    """Withdrawal flow tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_withdrawal_minimum_validation(self):
        """POST /api/wallet/withdraw - validates minimum £10"""
        response = requests.post(f"{BASE_URL}/api/wallet/withdraw", 
            json={"amount": 5.0, "method": "bank_transfer", "bank_details": "Test IBAN"},
            headers=self.headers
        )
        assert response.status_code == 400, f"Should reject amount below minimum: {response.text}"
        assert "Minimum" in response.json().get("detail", ""), "Error should mention minimum"
        print("✓ Minimum withdrawal validation works")
    
    def test_withdrawal_insufficient_balance(self):
        """POST /api/wallet/withdraw - validates sufficient balance"""
        # Try to withdraw more than balance
        response = requests.post(f"{BASE_URL}/api/wallet/withdraw", 
            json={"amount": 999999.0, "method": "bank_transfer", "bank_details": "Test IBAN"},
            headers=self.headers
        )
        assert response.status_code == 400, f"Should reject insufficient balance: {response.text}"
        assert "Insufficient" in response.json().get("detail", "") or "balance" in response.json().get("detail", "").lower(), "Error should mention balance"
        print("✓ Insufficient balance validation works")


class TestAdminWalletEndpoints:
    """Admin wallet management endpoints tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_get_all_withdrawals(self):
        """GET /api/admin/wallet/withdrawals - admin view all withdrawals"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/withdrawals", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"✓ Admin can view {len(data)} withdrawal requests")
    
    def test_admin_get_withdrawals_filtered_by_status(self):
        """GET /api/admin/wallet/withdrawals?status=pending - filter by status"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/withdrawals?status=pending", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        # All returned items should have pending status
        for wd in data:
            assert wd.get("status") == "pending", f"Expected pending status, got {wd.get('status')}"
        print(f"✓ Admin can filter withdrawals by status (found {len(data)} pending)")
    
    def test_admin_get_bonus_settings(self):
        """GET /api/admin/wallet/bonus-settings - get deposit bonus config"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/bonus-settings", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "active" in data, "Response should contain 'active' field"
        assert "bonus_percent" in data, "Response should contain 'bonus_percent' field"
        assert "bonus_max" in data, "Response should contain 'bonus_max' field"
        print(f"✓ Admin bonus settings: active={data['active']}, {data['bonus_percent']}% (max £{data['bonus_max']})")
    
    def test_admin_update_bonus_settings(self):
        """PUT /api/admin/wallet/bonus-settings - set deposit bonus config"""
        # First get current settings
        get_response = requests.get(f"{BASE_URL}/api/admin/wallet/bonus-settings", headers=self.headers)
        original_settings = get_response.json()
        
        # Update settings
        new_settings = {
            "active": True,
            "bonus_percent": 15.0,
            "bonus_max": 25.0
        }
        response = requests.put(f"{BASE_URL}/api/admin/wallet/bonus-settings", 
            json=new_settings,
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("bonus_percent") == 15.0, "Bonus percent should be updated"
        assert data.get("bonus_max") == 25.0, "Bonus max should be updated"
        print("✓ Admin can update bonus settings")
        
        # Verify the change persisted
        verify_response = requests.get(f"{BASE_URL}/api/admin/wallet/bonus-settings", headers=self.headers)
        verify_data = verify_response.json()
        assert verify_data.get("bonus_percent") == 15.0, "Bonus percent should persist"
        print("✓ Bonus settings persisted correctly")
        
        # Restore original settings
        requests.put(f"{BASE_URL}/api/admin/wallet/bonus-settings", 
            json=original_settings,
            headers=self.headers
        )
    
    def test_admin_get_wallet_stats(self):
        """GET /api/admin/wallet/stats - wallet statistics"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/stats", headers=self.headers)
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert "total_deposits" in data, "Response should contain 'total_deposits'"
        assert "total_withdrawals" in data, "Response should contain 'total_withdrawals'"
        assert "pending_withdrawals" in data, "Response should contain 'pending_withdrawals'"
        assert "total_user_balances" in data, "Response should contain 'total_user_balances'"
        print(f"✓ Wallet stats: deposits=£{data['total_deposits']}, withdrawals=£{data['total_withdrawals']}, pending={data['pending_withdrawals']}")
    
    def test_admin_adjust_wallet(self):
        """POST /api/admin/wallet/adjust - admin add/subtract funds from user wallet"""
        # Get current balance first
        balance_response = requests.get(f"{BASE_URL}/api/wallet/balance", headers=self.headers)
        original_balance = balance_response.json()["balance"]
        
        # Add funds
        response = requests.post(f"{BASE_URL}/api/admin/wallet/adjust", 
            json={
                "user_id": self.user["user_id"],
                "amount": 5.0,
                "reason": "TEST_adjustment_add"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("success") == True, "Response should indicate success"
        assert data.get("new_balance") == original_balance + 5.0, "Balance should increase by 5"
        print(f"✓ Admin added £5 to wallet (new balance: £{data['new_balance']})")
        
        # Subtract funds to restore
        response = requests.post(f"{BASE_URL}/api/admin/wallet/adjust", 
            json={
                "user_id": self.user["user_id"],
                "amount": -5.0,
                "reason": "TEST_adjustment_subtract"
            },
            headers=self.headers
        )
        assert response.status_code == 200, f"Failed: {response.text}"
        data = response.json()
        assert data.get("new_balance") == original_balance, "Balance should be restored"
        print(f"✓ Admin subtracted £5 from wallet (restored to: £{data['new_balance']})")
    
    def test_admin_adjust_wallet_negative_balance_prevention(self):
        """POST /api/admin/wallet/adjust - prevents negative balance"""
        response = requests.post(f"{BASE_URL}/api/admin/wallet/adjust", 
            json={
                "user_id": self.user["user_id"],
                "amount": -999999.0,
                "reason": "TEST_negative_balance_attempt"
            },
            headers=self.headers
        )
        assert response.status_code == 400, f"Should reject negative balance: {response.text}"
        assert "negative" in response.json().get("detail", "").lower(), "Error should mention negative balance"
        print("✓ Admin wallet adjust prevents negative balance")


class TestAdminWithdrawalApproval:
    """Admin withdrawal approval/rejection tests"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Login as admin to get token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        self.token = data["token"]
        self.user = data["user"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    def test_admin_approve_nonexistent_withdrawal(self):
        """POST /api/admin/wallet/withdrawal/{id}/approve - handles nonexistent withdrawal"""
        response = requests.post(f"{BASE_URL}/api/admin/wallet/withdrawal/nonexistent_id/approve", 
            headers=self.headers
        )
        assert response.status_code == 404, f"Should return 404 for nonexistent: {response.text}"
        print("✓ Admin approve handles nonexistent withdrawal correctly")
    
    def test_admin_reject_nonexistent_withdrawal(self):
        """POST /api/admin/wallet/withdrawal/{id}/reject - handles nonexistent withdrawal"""
        response = requests.post(f"{BASE_URL}/api/admin/wallet/withdrawal/nonexistent_id/reject", 
            headers=self.headers
        )
        assert response.status_code == 404, f"Should return 404 for nonexistent: {response.text}"
        print("✓ Admin reject handles nonexistent withdrawal correctly")


class TestWalletAuthRequired:
    """Test that wallet endpoints require authentication"""
    
    def test_wallet_balance_requires_auth(self):
        """GET /api/wallet/balance - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wallet/balance")
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Wallet balance requires authentication")
    
    def test_wallet_transactions_requires_auth(self):
        """GET /api/wallet/transactions - requires authentication"""
        response = requests.get(f"{BASE_URL}/api/wallet/transactions")
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Wallet transactions requires authentication")
    
    def test_wallet_deposit_requires_auth(self):
        """POST /api/wallet/deposit - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/wallet/deposit", json={"amount": 10.0})
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Wallet deposit requires authentication")
    
    def test_wallet_withdraw_requires_auth(self):
        """POST /api/wallet/withdraw - requires authentication"""
        response = requests.post(f"{BASE_URL}/api/wallet/withdraw", 
            json={"amount": 10.0, "method": "bank_transfer", "bank_details": "Test"})
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Wallet withdraw requires authentication")
    
    def test_admin_wallet_withdrawals_requires_admin(self):
        """GET /api/admin/wallet/withdrawals - requires admin"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/withdrawals")
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Admin wallet withdrawals requires authentication")
    
    def test_admin_wallet_stats_requires_admin(self):
        """GET /api/admin/wallet/stats - requires admin"""
        response = requests.get(f"{BASE_URL}/api/admin/wallet/stats")
        assert response.status_code == 401, f"Should require auth: {response.text}"
        print("✓ Admin wallet stats requires authentication")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
