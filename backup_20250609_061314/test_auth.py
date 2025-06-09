#!/usr/bin/env python3
"""
CineFluent API Authentication Test Script
Run this script to test your auth endpoints locally and on Railway
"""

import requests
import json
import time
from typing import Dict, Any

# Configuration
LOCAL_URL = "http://localhost:8000"
RAILWAY_URL = "https://cinefluent-api-production.up.railway.app"

# Test user data
TEST_USER = {
    "email": "test@cinefluent.com",
    "password": "TestPass123!",
    "full_name": "Test User"
}

def test_endpoint(url: str, method: str = "GET", data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
    """Test an API endpoint and return results"""
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=10)
        else:
            response = requests.get(url, headers=headers, timeout=10)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "error": None
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": str(e)
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "status_code": response.status_code,
            "data": {"raw": response.text},
            "error": f"JSON decode error: {str(e)}"
        }

def run_auth_tests(base_url: str) -> Dict[str, Any]:
    """Run comprehensive authentication tests"""
    print(f"\n🧪 Testing API at: {base_url}")
    results = {}
    
    # Test 1: Health Check
    print("1️⃣ Testing health check...")
    health_result = test_endpoint(f"{base_url}/")
    results["health"] = health_result
    
    if health_result["success"]:
        print(f"   ✅ Health check passed ({health_result['status_code']})")
    else:
        print(f"   ❌ Health check failed: {health_result['error']}")
        return results
    
    # Test 2: API Health Check
    print("2️⃣ Testing API health...")
    api_health_result = test_endpoint(f"{base_url}/api/v1/health")
    results["api_health"] = api_health_result
    
    if api_health_result["success"]:
        print(f"   ✅ API health check passed ({api_health_result['status_code']})")
        print(f"   📊 Status: {api_health_result['data'].get('status', 'unknown')}")
    else:
        print(f"   ❌ API health check failed: {api_health_result['error']}")
    
    # Test 3: User Registration
    print("3️⃣ Testing user registration...")
    register_result = test_endpoint(
        f"{base_url}/api/v1/auth/register",
        method="POST",
        data=TEST_USER
    )
    results["register"] = register_result
    
    if register_result["success"] and register_result["status_code"] in [200, 201]:
        print(f"   ✅ Registration passed ({register_result['status_code']})")
        print(f"   👤 User ID: {register_result['data'].get('user', {}).get('id', 'unknown')}")
    elif register_result["status_code"] == 409:
        print(f"   ⚠️  User already exists ({register_result['status_code']}) - continuing with login test")
    else:
        print(f"   ❌ Registration failed ({register_result['status_code']}): {register_result['data']}")
    
    # Test 4: User Login
    print("4️⃣ Testing user login...")
    login_data = {
        "email": TEST_USER["email"],
        "password": TEST_USER["password"]
    }
    
    login_result = test_endpoint(
        f"{base_url}/api/v1/auth/login",
        method="POST",
        data=login_data
    )
    results["login"] = login_result
    
    access_token = None
    if login_result["success"] and login_result["status_code"] == 200:
        print(f"   ✅ Login passed ({login_result['status_code']})")
        access_token = login_result["data"].get("access_token")
        if access_token:
            print(f"   🔑 Access token received (length: {len(access_token)})")
        else:
            print(f"   ⚠️  No access token in response")
    else:
        print(f"   ❌ Login failed ({login_result['status_code']}): {login_result['data']}")
    
    # Test 5: Get Current User (Protected Route)
    if access_token:
        print("5️⃣ Testing protected route (/auth/me)...")
        headers = {"Authorization": f"Bearer {access_token}"}
        
        me_result = test_endpoint(
            f"{base_url}/api/v1/auth/me",
            headers=headers
        )
        results["me"] = me_result
        
        if me_result["success"] and me_result["status_code"] == 200:
            print(f"   ✅ Protected route passed ({me_result['status_code']})")
            user_data = me_result["data"].get("user", {})
            profile_data = me_result["data"].get("profile", {})
            print(f"   👤 User: {user_data.get('email', 'unknown')}")
            print(f"   📋 Profile: {profile_data.get('username', 'unknown')}")
        else:
            print(f"   ❌ Protected route failed ({me_result['status_code']}): {me_result['data']}")
    else:
        print("5️⃣ Skipping protected route test (no access token)")
        results["me"] = {"success": False, "error": "No access token available"}
    
    # Test 6: Movies Endpoint (Public)
    print("6️⃣ Testing movies endpoint...")
    movies_result = test_endpoint(f"{base_url}/api/v1/movies")
    results["movies"] = movies_result
    
    if movies_result["success"] and movies_result["status_code"] == 200:
        print(f"   ✅ Movies endpoint passed ({movies_result['status_code']})")
        movies_data = movies_result["data"]
        total_movies = movies_data.get("total", 0)
        returned_movies = len(movies_data.get("movies", []))
        print(f"   🎬 Movies: {returned_movies} returned, {total_movies} total")
    else:
        print(f"   ❌ Movies endpoint failed ({movies_result['status_code']}): {movies_result['data']}")
    
    return results

def print_summary(local_results: Dict, railway_results: Dict):
    """Print test summary"""
    print("\n" + "="*60)
    print("📊 TEST SUMMARY")
    print("="*60)
    
    tests = ["health", "api_health", "register", "login", "me", "movies"]
    
    print(f"{'Test':<20} {'Local':<15} {'Railway':<15}")
    print("-" * 50)
    
    for test in tests:
        local_status = "✅ PASS" if local_results.get(test, {}).get("success") else "❌ FAIL"
        railway_status = "✅ PASS" if railway_results.get(test, {}).get("success") else "❌ FAIL"
        
        print(f"{test:<20} {local_status:<15} {railway_status:<15}")
    
    # Overall status
    local_auth_working = (
        local_results.get("login", {}).get("success") and 
        local_results.get("me", {}).get("success")
    )
    
    railway_auth_working = (
        railway_results.get("login", {}).get("success") and 
        railway_results.get("me", {}).get("success")
    )
    
    print("\n" + "="*60)
    if railway_auth_working:
        print("🎉 SUCCESS! Authentication is working on Railway!")
        print("✅ Your frontend can now successfully:")
        print("   • Register new users")
        print("   • Login existing users") 
        print("   • Access protected routes")
        print("   • Retrieve user profiles")
    else:
        print("❌ Authentication needs debugging on Railway")
        
    if local_auth_working:
        print("✅ Local development server is working correctly")
    else:
        print("❌ Local development server needs debugging")

def main():
    """Run all authentication tests"""
    print("🔐 CineFluent API Authentication Test Suite")
    print("=" * 60)
    
    # Test locally first (if available)
    print("\n🏠 TESTING LOCAL DEVELOPMENT SERVER")
    local_results = run_auth_tests(LOCAL_URL)
    
    # Test Railway deployment
    print(f"\n🚀 TESTING RAILWAY DEPLOYMENT")
    railway_results = run_auth_tests(RAILWAY_URL)
    
    # Print comprehensive summary
    print_summary(local_results, railway_results)
    
    # Specific Railway recommendations
    if not railway_results.get("login", {}).get("success"):
        print(f"\n🔧 DEBUGGING TIPS:")
        print("1. Check Railway environment variables are set correctly")
        print("2. Verify Supabase credentials in Railway dashboard")
        print("3. Check Railway logs: `railway logs`")
        print("4. Ensure database connection is working")

if __name__ == "__main__":
    main()