#!/usr/bin/env python3

import requests
import sys
import json
from datetime import datetime

# Test configuration
BACKEND_URL = "http://localhost:8001"  # Local backend for testing
API_BASE = f"{BACKEND_URL}/api"

class ZektrixBackendTester:
    def __init__(self):
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []
        
    def log_test(self, name, success, message="", expected="", actual=""):
        """Log test result"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
        
        result = {
            "test_name": name,
            "success": success,
            "message": message,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.test_results.append(result)
        
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} - {name}")
        if message:
            print(f"   {message}")
        if not success and expected and actual:
            print(f"   Expected: {expected}")
            print(f"   Actual: {actual}")
        print()
        
    def test_health_endpoint(self):
        """Test /api/health endpoint"""
        try:
            response = requests.get(f"{API_BASE}/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if "status" in data and data["status"] == "ok":
                    self.log_test(
                        "Health Check", 
                        True, 
                        f"Health endpoint responding correctly: {data}"
                    )
                    return True
                else:
                    self.log_test(
                        "Health Check", 
                        False, 
                        f"Health response missing status field or not 'ok': {data}"
                    )
            else:
                self.log_test(
                    "Health Check", 
                    False, 
                    f"Health endpoint returned status {response.status_code}"
                )
        except Exception as e:
            self.log_test(
                "Health Check", 
                False, 
                f"Failed to connect to health endpoint: {str(e)}"
            )
        return False
        
    def test_competitions_endpoint(self):
        """Test /api/competitions endpoint and verify competition_type field"""
        try:
            # Test basic competitions endpoint
            response = requests.get(f"{API_BASE}/competitions", timeout=10)
            
            if response.status_code != 200:
                self.log_test(
                    "Competitions API", 
                    False, 
                    f"Competitions endpoint returned status {response.status_code}"
                )
                return False
            
            try:
                competitions = response.json()
                self.log_test(
                    "Competitions API", 
                    True, 
                    f"Retrieved {len(competitions)} competitions"
                )
            except json.JSONDecodeError:
                self.log_test(
                    "Competitions API", 
                    False, 
                    "Failed to parse JSON response"
                )
                return False
            
            # Test competition_type field presence and values
            if not competitions:
                self.log_test(
                    "Competition Type Field", 
                    False, 
                    "No competitions found to test competition_type field"
                )
                return False
            
            # Check each competition for competition_type field
            valid_types = ['classic', 'instant_win', 'instant', 'autodraw']
            type_issues = []
            valid_competitions = 0
            
            for i, comp in enumerate(competitions[:10]):  # Test first 10
                comp_id = comp.get('competition_id', f'comp_{i}')
                comp_type = comp.get('competition_type')
                
                if comp_type is None:
                    type_issues.append(f"Competition {comp_id} missing competition_type field")
                elif comp_type not in valid_types:
                    type_issues.append(f"Competition {comp_id} has invalid competition_type: {comp_type}")
                else:
                    valid_competitions += 1
            
            if type_issues:
                self.log_test(
                    "Competition Type Field", 
                    False, 
                    f"Found {len(type_issues)} issues with competition_type field",
                    "All competitions should have valid competition_type",
                    "; ".join(type_issues[:3])  # Show first 3 issues
                )
            else:
                self.log_test(
                    "Competition Type Field", 
                    True, 
                    f"All {valid_competitions} tested competitions have valid competition_type field"
                )
            
            # Test filtering by competition_type
            for comp_type in ['classic', 'instant_win']:
                try:
                    filter_response = requests.get(f"{API_BASE}/competitions?competition_type={comp_type}", timeout=10)
                    if filter_response.status_code == 200:
                        filtered_comps = filter_response.json()
                        self.log_test(
                            f"Competition Type Filter ({comp_type})", 
                            True, 
                            f"Filter by {comp_type} returned {len(filtered_comps)} competitions"
                        )
                    else:
                        self.log_test(
                            f"Competition Type Filter ({comp_type})", 
                            False, 
                            f"Filter endpoint returned status {filter_response.status_code}"
                        )
                except Exception as e:
                    self.log_test(
                        f"Competition Type Filter ({comp_type})", 
                        False, 
                        f"Error testing filter: {str(e)}"
                    )
            
            return len(type_issues) == 0
            
        except Exception as e:
            self.log_test(
                "Competitions API", 
                False, 
                f"Failed to connect to competitions endpoint: {str(e)}"
            )
            return False
    
    def test_auth_endpoints(self):
        """Test authentication endpoints basic availability"""
        auth_endpoints = [
            "/auth/register",
            "/auth/login", 
            "/auth/me"
        ]
        
        for endpoint in auth_endpoints:
            try:
                response = requests.post(f"{API_BASE}{endpoint}", json={}, timeout=10)
                # We expect auth failures, just checking if endpoints exist
                if response.status_code in [400, 401, 422]:  # Expected errors for invalid data
                    self.log_test(
                        f"Auth Endpoint {endpoint}", 
                        True, 
                        f"Endpoint exists (status {response.status_code})"
                    )
                elif response.status_code == 405:  # Method not allowed
                    # Try GET for /auth/me
                    if endpoint == "/auth/me":
                        get_response = requests.get(f"{API_BASE}{endpoint}", timeout=10)
                        if get_response.status_code in [401, 403]:
                            self.log_test(
                                f"Auth Endpoint {endpoint}", 
                                True, 
                                f"GET endpoint exists (status {get_response.status_code})"
                            )
                        else:
                            self.log_test(
                                f"Auth Endpoint {endpoint}", 
                                False, 
                                f"Unexpected GET status {get_response.status_code}"
                            )
                    else:
                        self.log_test(
                            f"Auth Endpoint {endpoint}", 
                            False, 
                            f"Method not allowed for POST {response.status_code}"
                        )
                else:
                    self.log_test(
                        f"Auth Endpoint {endpoint}", 
                        False, 
                        f"Unexpected status code {response.status_code}"
                    )
            except Exception as e:
                self.log_test(
                    f"Auth Endpoint {endpoint}", 
                    False, 
                    f"Connection error: {str(e)}"
                )
    
    def run_all_tests(self):
        """Run all backend tests"""
        print("=" * 60)
        print("🚀 ZEKTRIX UK BACKEND API TESTS")
        print("=" * 60)
        print(f"Testing backend at: {BACKEND_URL}")
        print()
        
        # Core functionality tests
        self.test_health_endpoint()
        self.test_competitions_endpoint() 
        self.test_auth_endpoints()
        
        print("=" * 60)
        print(f"📊 TEST SUMMARY: {self.tests_passed}/{self.tests_run} PASSED")
        print("=" * 60)
        
        return self.tests_passed == self.tests_run

def main():
    tester = ZektrixBackendTester()
    success = tester.run_all_tests()
    
    # Save detailed results
    with open("/app/test_reports/backend_test_results.json", "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "backend_url": BACKEND_URL,
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": tester.tests_passed / max(tester.tests_run, 1),
            "results": tester.test_results
        }, f, indent=2)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())