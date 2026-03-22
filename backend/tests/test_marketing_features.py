# -*- coding: utf-8 -*-
"""
Test Marketing Features: Bundle Deals, Push Campaigns, TikTok Live Draw, Advanced Analytics
Tests for the 4 new features implemented in marketing.py
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Admin credentials
ADMIN_EMAIL = "contact@x67digital.com"
ADMIN_PASSWORD = "Credcada1."


@pytest.fixture(scope="module")
def api_client():
    """Shared requests session"""
    session = requests.Session()
    session.headers.update({"Content-Type": "application/json"})
    return session


@pytest.fixture(scope="module")
def admin_token(api_client):
    """Get admin authentication token"""
    response = api_client.post(f"{BASE_URL}/api/auth/login", json={
        "email": ADMIN_EMAIL,
        "password": ADMIN_PASSWORD
    })
    if response.status_code == 200:
        return response.json().get("token")
    pytest.skip(f"Admin authentication failed: {response.status_code} - {response.text}")


@pytest.fixture(scope="module")
def admin_client(api_client, admin_token):
    """Session with admin auth header"""
    api_client.headers.update({"Authorization": f"Bearer {admin_token}"})
    return api_client


# ==================== BUNDLE DEALS TESTS ====================

class TestBundleDeals:
    """Tests for Bundle Deals feature"""
    
    def test_get_public_bundles(self, api_client):
        """GET /api/bundles - Public endpoint returns active bundles"""
        response = api_client.get(f"{BASE_URL}/api/bundles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify bundle structure if bundles exist
        if len(data) > 0:
            bundle = data[0]
            assert "bundle_id" in bundle, "Bundle should have bundle_id"
            assert "name" in bundle, "Bundle should have name"
            assert "quantity" in bundle, "Bundle should have quantity"
            assert "discount_percent" in bundle, "Bundle should have discount_percent"
            assert "is_active" in bundle, "Bundle should have is_active"
            assert bundle["is_active"] == True, "Public endpoint should only return active bundles"
            print(f"Found {len(data)} active bundles")
    
    def test_admin_get_all_bundles(self, admin_client):
        """GET /api/admin/bundles - Admin can get all bundles"""
        response = admin_client.get(f"{BASE_URL}/api/admin/bundles")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Admin sees {len(data)} total bundles")
    
    def test_admin_create_bundle(self, admin_client):
        """POST /api/admin/bundles - Admin can create a bundle"""
        test_bundle = {
            "name": f"TEST_Bundle_{uuid.uuid4().hex[:6]}",
            "quantity": 7,
            "discount_percent": 15.0,
            "is_active": True
        }
        
        response = admin_client.post(f"{BASE_URL}/api/admin/bundles", json=test_bundle)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "bundle_id" in data, "Response should contain bundle_id"
        assert data["name"] == test_bundle["name"], "Name should match"
        assert data["quantity"] == test_bundle["quantity"], "Quantity should match"
        assert data["discount_percent"] == test_bundle["discount_percent"], "Discount should match"
        
        # Store for cleanup
        pytest.test_bundle_id = data["bundle_id"]
        print(f"Created bundle: {data['bundle_id']}")
    
    def test_admin_update_bundle(self, admin_client):
        """PUT /api/admin/bundles/{bundle_id} - Admin can update a bundle"""
        if not hasattr(pytest, 'test_bundle_id'):
            pytest.skip("No test bundle created")
        
        update_data = {
            "name": "TEST_Updated_Bundle",
            "discount_percent": 25.0
        }
        
        response = admin_client.put(f"{BASE_URL}/api/admin/bundles/{pytest.test_bundle_id}", json=update_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Update should return success"
        print(f"Updated bundle: {pytest.test_bundle_id}")
    
    def test_admin_delete_bundle(self, admin_client):
        """DELETE /api/admin/bundles/{bundle_id} - Admin can delete a bundle"""
        if not hasattr(pytest, 'test_bundle_id'):
            pytest.skip("No test bundle created")
        
        response = admin_client.delete(f"{BASE_URL}/api/admin/bundles/{pytest.test_bundle_id}")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Delete should return success"
        print(f"Deleted bundle: {pytest.test_bundle_id}")
    
    def test_bundles_require_admin_auth(self, api_client):
        """Admin bundle endpoints require authentication"""
        # Remove auth header for this test
        headers = {"Content-Type": "application/json"}
        
        # POST should fail without auth
        response = requests.post(f"{BASE_URL}/api/admin/bundles", 
                                json={"name": "Test", "quantity": 1, "discount_percent": 10},
                                headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("Bundle admin endpoints properly require authentication")


# ==================== PUSH CAMPAIGNS TESTS ====================

class TestPushCampaigns:
    """Tests for Push Campaign Manager feature"""
    
    def test_get_campaign_history(self, admin_client):
        """GET /api/admin/campaigns - Returns campaign history"""
        response = admin_client.get(f"{BASE_URL}/api/admin/campaigns")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        
        # Verify campaign structure if campaigns exist
        if len(data) > 0:
            campaign = data[0]
            assert "campaign_id" in campaign, "Campaign should have campaign_id"
            assert "title" in campaign, "Campaign should have title"
            assert "message" in campaign, "Campaign should have message"
            assert "audience" in campaign, "Campaign should have audience"
            assert "sent_at" in campaign, "Campaign should have sent_at"
        print(f"Found {len(data)} campaigns in history")
    
    def test_get_audience_stats(self, admin_client):
        """GET /api/admin/campaigns/audience-stats - Returns audience numbers"""
        response = admin_client.get(f"{BASE_URL}/api/admin/campaigns/audience-stats")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "all" in data, "Response should have 'all' count"
        assert "active" in data, "Response should have 'active' count"
        assert "subscribers" in data, "Response should have 'subscribers' count"
        
        assert isinstance(data["all"], int), "'all' should be an integer"
        assert isinstance(data["active"], int), "'active' should be an integer"
        assert isinstance(data["subscribers"], int), "'subscribers' should be an integer"
        
        print(f"Audience stats: all={data['all']}, active={data['active']}, subscribers={data['subscribers']}")
    
    def test_send_campaign(self, admin_client):
        """POST /api/admin/campaigns/send - Sends a push campaign"""
        campaign_data = {
            "title": "TEST Campaign",
            "message": "This is a test campaign message",
            "url": "https://zektrix.uk/test",
            "audience": "all"
        }
        
        response = admin_client.post(f"{BASE_URL}/api/admin/campaigns/send", json=campaign_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "success" in data, "Response should have success field"
        assert data["success"] == True, "Campaign send should succeed"
        assert "sent" in data, "Response should have sent count"
        assert "total" in data, "Response should have total count"
        
        print(f"Campaign sent: {data['sent']}/{data['total']} delivered")
    
    def test_campaigns_require_admin_auth(self, api_client):
        """Campaign endpoints require admin authentication"""
        headers = {"Content-Type": "application/json"}
        
        # GET campaigns should fail without auth
        response = requests.get(f"{BASE_URL}/api/admin/campaigns", headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        # GET audience stats should fail without auth
        response = requests.get(f"{BASE_URL}/api/admin/campaigns/audience-stats", headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        
        print("Campaign endpoints properly require admin authentication")


# ==================== TIKTOK LIVE DRAW TESTS ====================

class TestLiveDraw:
    """Tests for TikTok Live Draw feature"""
    
    def test_get_live_draw_status_public(self, api_client):
        """GET /api/live-draw - Public endpoint returns live draw status"""
        response = api_client.get(f"{BASE_URL}/api/live-draw")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "is_live" in data, "Response should have is_live field"
        assert isinstance(data["is_live"], bool), "is_live should be boolean"
        
        if data["is_live"]:
            assert "competition_id" in data, "Live draw should have competition_id"
            print(f"Live draw is ACTIVE for competition: {data.get('competition_id')}")
        else:
            print("No live draw currently active")
    
    def test_admin_set_live_draw(self, admin_client):
        """PUT /api/admin/live-draw - Admin can set live draw status"""
        # First, get a competition ID to use
        comps_response = admin_client.get(f"{BASE_URL}/api/competitions")
        comps = comps_response.json()
        
        if not comps:
            pytest.skip("No competitions available for live draw test")
        
        comp_id = comps[0]["competition_id"]
        
        # Enable live draw
        live_draw_data = {
            "competition_id": comp_id,
            "is_live": True,
            "tiktok_live_url": "https://www.tiktok.com/@zektrix/live"
        }
        
        response = admin_client.put(f"{BASE_URL}/api/admin/live-draw", json=live_draw_data)
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert data.get("success") == True, "Setting live draw should succeed"
        print(f"Live draw enabled for competition: {comp_id}")
        
        # Verify it's now live
        verify_response = admin_client.get(f"{BASE_URL}/api/live-draw")
        verify_data = verify_response.json()
        assert verify_data["is_live"] == True, "Live draw should now be active"
        
        # Disable live draw (cleanup)
        disable_data = {
            "competition_id": comp_id,
            "is_live": False,
            "tiktok_live_url": None
        }
        admin_client.put(f"{BASE_URL}/api/admin/live-draw", json=disable_data)
        print("Live draw disabled (cleanup)")
    
    def test_live_draw_admin_auth_required(self, api_client):
        """PUT /api/admin/live-draw requires admin authentication"""
        headers = {"Content-Type": "application/json"}
        
        response = requests.put(f"{BASE_URL}/api/admin/live-draw", 
                               json={"competition_id": "test", "is_live": True},
                               headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("Live draw admin endpoint properly requires authentication")


# ==================== ADVANCED ANALYTICS TESTS ====================

class TestAdvancedAnalytics:
    """Tests for Advanced Analytics feature"""
    
    def test_get_advanced_analytics(self, admin_client):
        """GET /api/admin/analytics/advanced - Returns detailed analytics"""
        response = admin_client.get(f"{BASE_URL}/api/admin/analytics/advanced")
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        
        # Verify KPI fields
        assert "conversion_rate" in data, "Should have conversion_rate"
        assert "total_users" in data, "Should have total_users"
        assert "unique_buyers" in data, "Should have unique_buyers"
        assert "aov" in data, "Should have AOV (average order value)"
        assert "total_revenue" in data, "Should have total_revenue"
        assert "total_orders" in data, "Should have total_orders"
        
        # Verify retention fields
        assert "repeat_rate" in data, "Should have repeat_rate"
        assert "repeat_buyers" in data, "Should have repeat_buyers"
        assert "loyal_buyers" in data, "Should have loyal_buyers"
        
        # Verify revenue breakdown
        assert "revenue_by_day" in data, "Should have revenue_by_day"
        assert isinstance(data["revenue_by_day"], list), "revenue_by_day should be a list"
        
        # Verify top spenders
        assert "top_spenders" in data, "Should have top_spenders"
        assert isinstance(data["top_spenders"], list), "top_spenders should be a list"
        
        # Verify subscription stats
        assert "active_subscriptions" in data, "Should have active_subscriptions"
        assert "total_subscriptions" in data, "Should have total_subscriptions"
        
        print(f"Analytics: conversion={data['conversion_rate']}%, AOV=£{data['aov']}, revenue=£{data['total_revenue']}")
        print(f"Retention: repeat_rate={data['repeat_rate']}%, repeat_buyers={data['repeat_buyers']}, loyal={data['loyal_buyers']}")
        print(f"Top spenders: {len(data['top_spenders'])} users")
    
    def test_analytics_data_types(self, admin_client):
        """Verify analytics data types are correct"""
        response = admin_client.get(f"{BASE_URL}/api/admin/analytics/advanced")
        data = response.json()
        
        # Numeric fields should be numbers
        assert isinstance(data["conversion_rate"], (int, float)), "conversion_rate should be numeric"
        assert isinstance(data["total_users"], int), "total_users should be int"
        assert isinstance(data["unique_buyers"], int), "unique_buyers should be int"
        assert isinstance(data["aov"], (int, float)), "aov should be numeric"
        assert isinstance(data["total_revenue"], (int, float)), "total_revenue should be numeric"
        assert isinstance(data["repeat_rate"], (int, float)), "repeat_rate should be numeric"
        
        # Verify revenue_by_day structure
        if data["revenue_by_day"]:
            day_data = data["revenue_by_day"][0]
            assert "date" in day_data, "Day data should have date"
            assert "revenue" in day_data, "Day data should have revenue"
            assert "orders" in day_data, "Day data should have orders"
        
        # Verify top_spenders structure
        if data["top_spenders"]:
            spender = data["top_spenders"][0]
            assert "username" in spender, "Spender should have username"
            assert "total_spent" in spender, "Spender should have total_spent"
            assert "orders" in spender, "Spender should have orders"
        
        print("All analytics data types verified correctly")
    
    def test_analytics_requires_admin_auth(self, api_client):
        """Advanced analytics requires admin authentication"""
        headers = {"Content-Type": "application/json"}
        
        response = requests.get(f"{BASE_URL}/api/admin/analytics/advanced", headers=headers)
        assert response.status_code in [401, 403], f"Expected 401/403 without auth, got {response.status_code}"
        print("Advanced analytics endpoint properly requires admin authentication")


# ==================== INTEGRATION TESTS ====================

class TestMarketingIntegration:
    """Integration tests for marketing features"""
    
    def test_bundles_appear_in_public_api(self, admin_client, api_client):
        """Bundles created by admin appear in public API"""
        # Create a test bundle
        test_bundle = {
            "name": f"TEST_Integration_{uuid.uuid4().hex[:6]}",
            "quantity": 5,
            "discount_percent": 10.0,
            "is_active": True
        }
        
        create_response = admin_client.post(f"{BASE_URL}/api/admin/bundles", json=test_bundle)
        assert create_response.status_code == 200
        bundle_id = create_response.json()["bundle_id"]
        
        # Verify it appears in public API
        public_response = api_client.get(f"{BASE_URL}/api/bundles")
        public_bundles = public_response.json()
        
        found = any(b["bundle_id"] == bundle_id for b in public_bundles)
        assert found, "Created bundle should appear in public API"
        
        # Cleanup
        admin_client.delete(f"{BASE_URL}/api/admin/bundles/{bundle_id}")
        print("Integration test passed: bundles sync between admin and public API")
    
    def test_campaign_appears_in_history(self, admin_client):
        """Sent campaign appears in campaign history"""
        # Get initial campaign count
        initial_response = admin_client.get(f"{BASE_URL}/api/admin/campaigns")
        initial_count = len(initial_response.json())
        
        # Send a campaign
        campaign_data = {
            "title": f"TEST_History_{uuid.uuid4().hex[:6]}",
            "message": "Integration test campaign",
            "url": "https://zektrix.uk",
            "audience": "all"
        }
        
        send_response = admin_client.post(f"{BASE_URL}/api/admin/campaigns/send", json=campaign_data)
        assert send_response.status_code == 200
        
        # Verify it appears in history
        history_response = admin_client.get(f"{BASE_URL}/api/admin/campaigns")
        new_count = len(history_response.json())
        
        assert new_count > initial_count, "Campaign should appear in history"
        
        # Verify the campaign details
        campaigns = history_response.json()
        found = any(c["title"] == campaign_data["title"] for c in campaigns)
        assert found, "Campaign with correct title should be in history"
        
        print("Integration test passed: campaigns appear in history after sending")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
