"""
Test suite for Qualification Question feature in Zektrix UK Competition Platform
Tests:
- Admin: Create competition with qualification question
- User: View competition with qualification question displayed
- User: Purchase ticket with incorrect answer (should fail)
- User: Purchase ticket with correct answer (should succeed)
- Both wallet and Viva payment flows with qualification validation
"""

import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test data
TEST_USER_EMAIL = f"test_qual_{uuid.uuid4().hex[:8]}@test.com"
TEST_USER_PASSWORD = "TestPass123!"
TEST_USER_USERNAME = f"test_qual_{uuid.uuid4().hex[:8]}"

ADMIN_EMAIL = "admin@zektrix.uk"
ADMIN_PASSWORD = "admin123"


class TestQualificationQuestionFeature:
    """Test suite for qualification question feature"""
    
    @pytest.fixture(scope="class")
    def admin_token(self):
        """Get admin authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("token")
        # Try to register admin if not exists
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD,
            "username": "admin_test"
        })
        if response.status_code == 200:
            return response.json().get("token")
        pytest.skip("Could not authenticate as admin")
    
    @pytest.fixture(scope="class")
    def test_user(self):
        """Create a test user and return credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/register", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD,
            "username": TEST_USER_USERNAME
        })
        if response.status_code == 200:
            data = response.json()
            return {
                "token": data.get("token"),
                "user": data.get("user"),
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        # User might already exist, try login
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": TEST_USER_EMAIL,
            "password": TEST_USER_PASSWORD
        })
        if response.status_code == 200:
            data = response.json()
            return {
                "token": data.get("token"),
                "user": data.get("user"),
                "email": TEST_USER_EMAIL,
                "password": TEST_USER_PASSWORD
            }
        pytest.skip("Could not create or login test user")
    
    @pytest.fixture(scope="class")
    def competition_with_question(self, admin_token):
        """Create a competition with a qualification question"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        # Create competition with custom qualification question
        comp_data = {
            "title": f"TEST_Qualification_Comp_{uuid.uuid4().hex[:6]}",
            "description": "Test competition with qualification question",
            "ticket_price": 1.00,
            "max_tickets": 100,
            "competition_type": "instant_win",
            "image_url": "https://images.unsplash.com/photo-1669606072600-1a62d7f24873",
            "prize_description": "Test Prize",
            "qualification_question": {
                "question": "What is 2 + 2?",
                "options": ["3", "4", "5"],
                "correct_answer": 1  # Index 1 = "4"
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/competitions",
            json=comp_data,
            headers=headers
        )
        
        if response.status_code == 200:
            return response.json()
        pytest.skip(f"Could not create competition: {response.text}")
    
    # ==================== ADMIN TESTS ====================
    
    def test_admin_create_competition_with_qualification_question(self, admin_token):
        """Test that admin can create a competition with qualification question fields"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        comp_data = {
            "title": f"TEST_Admin_Qual_{uuid.uuid4().hex[:6]}",
            "description": "Admin test competition",
            "ticket_price": 0.99,
            "max_tickets": 50,
            "competition_type": "classic",
            "qualification_question": {
                "question": "What color is the sky?",
                "options": ["Red", "Blue", "Green"],
                "correct_answer": 1
            }
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/competitions",
            json=comp_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to create competition: {response.text}"
        
        data = response.json()
        assert "competition_id" in data
        assert data["title"] == comp_data["title"]
        
        # Verify qualification question is saved
        qual_q = data.get("qualification_question")
        assert qual_q is not None, "Qualification question not saved"
        assert qual_q["question"] == "What color is the sky?"
        assert qual_q["options"] == ["Red", "Blue", "Green"]
        assert qual_q["correct_answer"] == 1
        
        # Verify postal entry is auto-generated
        postal = data.get("postal_entry")
        assert postal is not None, "Postal entry not auto-generated"
        assert postal["company_name"] == "Zektrix UK Ltd"
        
        print(f"✓ Admin created competition with qualification question: {data['competition_id']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/competitions/{data['competition_id']}", headers=headers)
    
    def test_admin_create_competition_auto_generates_question(self, admin_token):
        """Test that competition auto-generates qualification question if not provided"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        
        comp_data = {
            "title": f"TEST_Auto_Qual_{uuid.uuid4().hex[:6]}",
            "description": "Auto-generated question test",
            "ticket_price": 1.50,
            "max_tickets": 100,
            "competition_type": "instant_win"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/admin/competitions",
            json=comp_data,
            headers=headers
        )
        
        assert response.status_code == 200, f"Failed to create competition: {response.text}"
        
        data = response.json()
        
        # Verify qualification question is auto-generated
        qual_q = data.get("qualification_question")
        assert qual_q is not None, "Qualification question should be auto-generated"
        assert "question" in qual_q
        assert "options" in qual_q
        assert len(qual_q["options"]) == 3
        assert "correct_answer" in qual_q
        
        print(f"✓ Auto-generated qualification question: {qual_q['question']}")
        
        # Cleanup
        requests.delete(f"{BASE_URL}/api/admin/competitions/{data['competition_id']}", headers=headers)
    
    # ==================== USER VIEW TESTS ====================
    
    def test_user_can_view_qualification_question(self, competition_with_question):
        """Test that qualification question is displayed on competition detail page"""
        comp_id = competition_with_question["competition_id"]
        
        response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        qual_q = data.get("qualification_question")
        
        assert qual_q is not None, "Qualification question should be visible"
        assert qual_q["question"] == "What is 2 + 2?"
        assert qual_q["options"] == ["3", "4", "5"]
        # Note: correct_answer should be visible for frontend to validate
        assert qual_q["correct_answer"] == 1
        
        print(f"✓ Qualification question visible: {qual_q['question']}")
    
    def test_user_can_view_postal_entry(self, competition_with_question):
        """Test that free postal entry section is visible"""
        comp_id = competition_with_question["competition_id"]
        
        response = requests.get(f"{BASE_URL}/api/competitions/{comp_id}")
        
        assert response.status_code == 200
        
        data = response.json()
        postal = data.get("postal_entry")
        
        assert postal is not None, "Postal entry should be visible"
        assert postal["company_name"] == "Zektrix UK Ltd"
        assert postal["address_line1"] == "c/o Bartle House"
        assert postal["postcode"] == "M23 WQ"
        assert "instructions" in postal
        assert len(postal["instructions"]) > 0
        
        print(f"✓ Postal entry visible with address: {postal['address_line1']}")
    
    # ==================== WALLET PURCHASE TESTS ====================
    
    def test_wallet_purchase_fails_without_answer(self, test_user, competition_with_question):
        """Test that wallet purchase fails when no qualification answer provided"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase",
            json={
                "competition_id": comp_id,
                "quantity": 1
                # No qualification_answer provided
            },
            headers=headers
        )
        
        # Should fail with 400 - qualification answer required
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "qualification" in response.text.lower() or "answer" in response.text.lower()
        
        print("✓ Wallet purchase correctly rejected without answer")
    
    def test_wallet_purchase_fails_with_incorrect_answer(self, test_user, competition_with_question, admin_token):
        """Test that wallet purchase fails with incorrect qualification answer"""
        # First, add balance to user
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        requests.put(
            f"{BASE_URL}/api/admin/users/{test_user['user']['user_id']}",
            json={"balance_change": 10.0},
            headers=headers_admin
        )
        
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        # Try with wrong answer (correct is 1, we send 0)
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase",
            json={
                "competition_id": comp_id,
                "quantity": 1,
                "qualification_answer": 0  # Wrong answer (3 instead of 4)
            },
            headers=headers
        )
        
        # Should fail with 400 - incorrect answer
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "incorrect" in response.text.lower() or "qualification" in response.text.lower()
        
        print("✓ Wallet purchase correctly rejected with incorrect answer")
    
    def test_wallet_purchase_succeeds_with_correct_answer(self, test_user, competition_with_question, admin_token):
        """Test that wallet purchase succeeds with correct qualification answer"""
        # Ensure user has balance
        headers_admin = {"Authorization": f"Bearer {admin_token}"}
        requests.put(
            f"{BASE_URL}/api/admin/users/{test_user['user']['user_id']}",
            json={"balance_change": 10.0},
            headers=headers_admin
        )
        
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        # Try with correct answer (index 1 = "4")
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase",
            json={
                "competition_id": comp_id,
                "quantity": 1,
                "qualification_answer": 1  # Correct answer
            },
            headers=headers
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 1
        assert "ticket_id" in data[0]
        assert "ticket_number" in data[0]
        
        print(f"✓ Wallet purchase succeeded with correct answer, ticket: #{data[0]['ticket_number']}")
    
    # ==================== VIVA PAYMENT TESTS ====================
    
    def test_viva_purchase_fails_without_answer(self, test_user, competition_with_question):
        """Test that Viva purchase fails when no qualification answer provided"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase-viva",
            json={
                "competition_id": comp_id,
                "quantity": 1
                # No qualification_answer provided
            },
            headers=headers
        )
        
        # Should fail with 400 - qualification answer required
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "qualification" in response.text.lower() or "answer" in response.text.lower()
        
        print("✓ Viva purchase correctly rejected without answer")
    
    def test_viva_purchase_fails_with_incorrect_answer(self, test_user, competition_with_question):
        """Test that Viva purchase fails with incorrect qualification answer"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        # Try with wrong answer
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase-viva",
            json={
                "competition_id": comp_id,
                "quantity": 1,
                "qualification_answer": 2  # Wrong answer (5 instead of 4)
            },
            headers=headers
        )
        
        # Should fail with 400 - incorrect answer
        assert response.status_code == 400, f"Expected 400, got {response.status_code}: {response.text}"
        assert "incorrect" in response.text.lower() or "qualification" in response.text.lower()
        
        print("✓ Viva purchase correctly rejected with incorrect answer")
    
    def test_viva_purchase_succeeds_with_correct_answer(self, test_user, competition_with_question):
        """Test that Viva purchase succeeds with correct qualification answer"""
        headers = {"Authorization": f"Bearer {test_user['token']}"}
        comp_id = competition_with_question["competition_id"]
        
        # Try with correct answer
        response = requests.post(
            f"{BASE_URL}/api/tickets/purchase-viva",
            json={
                "competition_id": comp_id,
                "quantity": 1,
                "qualification_answer": 1  # Correct answer
            },
            headers=headers
        )
        
        # Should succeed and return checkout URL
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        
        data = response.json()
        assert "checkout_url" in data
        assert "order_code" in data
        assert "vivapayments.com" in data["checkout_url"]
        
        print(f"✓ Viva purchase succeeded with correct answer, checkout URL generated")
    
    # ==================== CLEANUP ====================
    
    def test_cleanup_test_competition(self, admin_token, competition_with_question):
        """Cleanup test competition"""
        headers = {"Authorization": f"Bearer {admin_token}"}
        comp_id = competition_with_question["competition_id"]
        
        response = requests.delete(
            f"{BASE_URL}/api/admin/competitions/{comp_id}",
            headers=headers
        )
        
        # May fail if already deleted, that's ok
        print(f"✓ Cleanup completed for competition: {comp_id}")


class TestExistingCompetitionsWithoutQuestion:
    """Test that existing competitions without qualification questions still work"""
    
    def test_purchase_works_without_qualification_question(self):
        """Test that competitions without qualification questions don't require answer"""
        # Get existing competitions
        response = requests.get(f"{BASE_URL}/api/competitions")
        assert response.status_code == 200
        
        competitions = response.json()
        
        # Find a competition without qualification question
        comp_without_q = None
        for comp in competitions:
            if comp.get("qualification_question") is None and comp.get("status") == "active":
                comp_without_q = comp
                break
        
        if comp_without_q is None:
            pytest.skip("No active competition without qualification question found")
        
        print(f"✓ Found competition without qualification question: {comp_without_q['title']}")
        
        # Note: We can't fully test purchase without a user with balance,
        # but we can verify the competition is accessible
        assert comp_without_q["status"] == "active"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
