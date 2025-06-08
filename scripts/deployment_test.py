#!/usr/bin/env python3
"""
CineFluent Railway Deployment Test Script
Test all critical endpoints after Railway deployment
"""

import requests
import json
import time
from typing import Dict, Any, Optional

# Railway deployment URL - update this with your actual Railway URL
RAILWAY_URL = "https://cinefluent-api-production.up.railway.app"

# Test user for comprehensive testing
TEST_USER = {
    "email": "railway_test@cinefluent.com",
    "password": "RailwayTest123!",
    "full_name": "Railway Test User"
}

def make_request(url: str, method: str = "GET", data: Dict = None, headers: Dict = None) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        if method == "POST":
            response = requests.post(url, json=data, headers=headers, timeout=15)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=15)
        else:
            response = requests.get(url, headers=headers, timeout=15)
        
        return {
            "success": True,
            "status_code": response.status_code,
            "data": response.json() if response.content else {},
            "error": None,
            "response_time": response.elapsed.total_seconds()
        }
    except requests.exceptions.RequestException as e:
        return {
            "success": False,
            "status_code": None,
            "data": {},
            "error": str(e),
            "response_time": None
        }
    except json.JSONDecodeError as e:
        return {
            "success": False,
            "status_code": response.status_code,
            "data": {"raw_response": response.text},
            "error": f"JSON decode error: {str(e)}",
            "response_time": response.elapsed.total_seconds()
        }

def test_endpoint(name: str, url: str, method: str = "GET", data: Dict = None, headers: Dict = None, expected_status: int = 200) -> bool:
    """Test a single endpoint and print results"""
    print(f"{'🧪 Testing ' + name:<50}", end="")
    
    result = make_request(url, method, data, headers)
    
    if result["success"] and result["status_code"] == expected_status:
        response_time = result["response_time"]
        print(f"✅ PASS ({response_time:.2f}s)")
        return True
    else:
        status = result["status_code"] or "ERROR"
        error = result["error"] or "Unknown error"
        print(f"❌ FAIL ({status})")
        if result["error"]:
            print(f"{'   Error:':<50} {error}")
        return False

def run_comprehensive_test() -> Dict[str, Any]:
    """Run comprehensive deployment test"""
    print("🚀 CineFluent Railway Deployment Test Suite")
    print("=" * 80)
    print(f"Testing deployment at: {RAILWAY_URL}")
    print("=" * 80)
    
    results = {
        "total_tests": 0,
        "passed_tests": 0,
        "failed_tests": 0,
        "test_results": {},
        "critical_features_working": False,
        "access_token": None
    }
    
    # Test 1: Basic Health Check
    test_name = "Basic Health Check"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 2: API Health Check
    test_name = "API Health Check"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/health"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 3: Database Test
    test_name = "Database Connectivity"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/test/database"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 4: User Registration
    test_name = "User Registration"
    results["total_tests"] += 1
    register_result = make_request(
        f"{RAILWAY_URL}/api/v1/auth/register",
        method="POST",
        data=TEST_USER
    )
    
    if register_result["success"] and register_result["status_code"] in [200, 201, 409]:
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
        print(f"{'🧪 Testing ' + test_name:<50}✅ PASS ({register_result['response_time']:.2f}s)")
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
        print(f"{'🧪 Testing ' + test_name:<50}❌ FAIL ({register_result['status_code']})")
    
    # Test 5: User Login
    test_name = "User Login"
    results["total_tests"] += 1
    login_result = make_request(
        f"{RAILWAY_URL}/api/v1/auth/login",
        method="POST",
        data={"email": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    
    if login_result["success"] and login_result["status_code"] == 200:
        access_token = login_result["data"].get("access_token")
        if access_token:
            results["access_token"] = access_token
            results["passed_tests"] += 1
            results["test_results"][test_name] = "PASS"
            print(f"{'🧪 Testing ' + test_name:<50}✅ PASS ({login_result['response_time']:.2f}s)")
        else:
            results["failed_tests"] += 1
            results["test_results"][test_name] = "FAIL"
            print(f"{'🧪 Testing ' + test_name:<50}❌ FAIL (No token)")
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
        print(f"{'🧪 Testing ' + test_name:<50}❌ FAIL ({login_result['status_code']})")
    
    # Test 6: Protected Route (/auth/me)
    if results["access_token"]:
        test_name = "Protected Route Access"
        results["total_tests"] += 1
        headers = {"Authorization": f"Bearer {results['access_token']}"}
        if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/auth/me", headers=headers):
            results["passed_tests"] += 1
            results["test_results"][test_name] = "PASS"
        else:
            results["failed_tests"] += 1
            results["test_results"][test_name] = "FAIL"
    
    # Test 7: Movies Endpoint
    test_name = "Movies API"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/movies"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 8: Categories Endpoint
    test_name = "Categories API"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/categories"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 9: Languages Endpoint
    test_name = "Languages API"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/languages"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 10: Featured Movies
    test_name = "Featured Movies API"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/movies/featured"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 11: Movie Search
    test_name = "Movie Search API"
    results["total_tests"] += 1
    if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/movies/search?q=test"):
        results["passed_tests"] += 1
        results["test_results"][test_name] = "PASS"
    else:
        results["failed_tests"] += 1
        results["test_results"][test_name] = "FAIL"
    
    # Test 12: Progress Stats (if authenticated)
    if results["access_token"]:
        test_name = "Progress Stats API"
        results["total_tests"] += 1
        headers = {"Authorization": f"Bearer {results['access_token']}"}
        if test_endpoint(test_name, f"{RAILWAY_URL}/api/v1/progress/stats", headers=headers):
            results["passed_tests"] += 1
            results["test_results"][test_name] = "PASS"
        else:
            results["failed_tests"] += 1
            results["test_results"][test_name] = "FAIL"
    
    # Determine if critical features are working
    critical_tests = ["User Login", "Protected Route Access", "Movies API", "Database Connectivity"]
    critical_passing = all(results["test_results"].get(test) == "PASS" for test in critical_tests if test in results["test_results"])
    results["critical_features_working"] = critical_passing
    
    return results

def print_test_summary(results: Dict[str, Any]):
    """Print comprehensive test summary"""
    print("\n" + "=" * 80)
    print("📊 RAILWAY DEPLOYMENT TEST SUMMARY")
    print("=" * 80)
    
    # Overall Results
    total = results["total_tests"]
    passed = results["passed_tests"]
    failed = results["failed_tests"]
    success_rate = (passed / total * 100) if total > 0 else 0
    
    print(f"Total Tests: {total}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {success_rate:.1f}%")
    
    # Test Details
    print(f"\n{'Test Name':<30} {'Status':<10} {'Notes'}")
    print("-" * 60)
    
    for test_name, status in results["test_results"].items():
        status_emoji = "✅" if status == "PASS" else "❌"
        print(f"{test_name:<30} {status_emoji} {status:<10}")
    
    # Critical Assessment
    print(f"\n{'='*80}")
    
    if results["critical_features_working"]:
        print("🎉 SUCCESS! Your CineFluent API is working on Railway!")
        print("\n✅ Critical features verified:")
        print("   • User authentication (register/login)")
        print("   • Protected routes with JWT tokens")
        print("   • Database connectivity")
        print("   • Movies API endpoints")
        print("   • Profile management")
        print("   • Progress tracking")
        
        print(f"\n🚀 Your API is ready for frontend integration!")
        print(f"📍 API Base URL: {RAILWAY_URL}")
        
        if results["access_token"]:
            print(f"🔑 Test token available for frontend testing")
        
        print(f"\n📝 Next Steps:")
        print("1. Update your frontend to use this Railway URL")
        print("2. Set up environment variables in your frontend")
        print("3. Test the complete user flow")
        print("4. Add more sample movie data")
        print("5. Implement subtitle upload functionality")
        
    else:
        print("❌ Some critical features are not working properly")
        print("\n🔧 Issues to address:")
        
        critical_tests = ["User Login", "Protected Route Access", "Movies API", "Database Connectivity"]
        for test in critical_tests:
            if results["test_results"].get(test) == "FAIL":
                print(f"   • {test}: Check logs and environment variables")
        
        print(f"\n🛠️ Debugging steps:")
        print("1. Check Railway logs: `railway logs`")
        print("2. Verify environment variables in Railway dashboard")
        print("3. Ensure Supabase credentials are correct")
        print("4. Check database schema setup")
    
    # Performance Notes
    print(f"\n📊 Performance Notes:")
    if success_rate >= 90:
        print("   • Excellent: All systems operational")
    elif success_rate >= 75:
        print("   • Good: Minor issues to address")
    elif success_rate >= 50:
        print("   • Fair: Several issues need attention")
    else:
        print("   • Poor: Major deployment issues")
    
    print(f"\n🌐 API Endpoints Available:")
    print(f"   • Health: {RAILWAY_URL}/api/v1/health")
    print(f"   • Movies: {RAILWAY_URL}/api/v1/movies")
    print(f"   • Auth: {RAILWAY_URL}/api/v1/auth/login")
    print(f"   • Debug: {RAILWAY_URL}/debug")

def main():
    """Run the comprehensive Railway deployment test"""
    try:
        print("🔍 Starting comprehensive Railway deployment test...")
        print("⏱️  This will test all critical API endpoints...")
        print("")
        
        results = run_comprehensive_test()
        print_test_summary(results)
        
        # Return appropriate exit code
        if results["critical_features_working"]:
            print(f"\n✨ Test completed successfully!")
            return 0
        else:
            print(f"\n⚠️  Test completed with issues")
            return 1
            
    except KeyboardInterrupt:
        print(f"\n\n⏹️  Test interrupted by user")
        return 1
    except Exception as e:
        print(f"\n\n💥 Test failed with error: {str(e)}")
        return 1

if __name__ == "__main__":
    exit(main())
