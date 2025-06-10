#!/usr/bin/env python3
"""
CineFluent API - Local Testing Script
Test the API endpoints to ensure everything is working
"""

import requests
import json
from datetime import datetime

# API Configuration
API_BASE_URL = "https://cinefluent-api-production.up.railway.app"
LOCAL_URL = "http://localhost:8000"

def test_endpoint(url, endpoint_name):
    """Test a single endpoint"""
    try:
        print(f"  Testing {endpoint_name}...")
        response = requests.get(url, timeout=10)
        
        if response.status_code == 200:
            print(f"  ✅ {endpoint_name} - OK")
            return True, response.json()
        else:
            print(f"  ❌ {endpoint_name} - Status: {response.status_code}")
            return False, None
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ {endpoint_name} - Error: {str(e)}")
        return False, None

def test_api_health(base_url):
    """Test API health and basic endpoints"""
    print(f"\n🎌 Testing CineFluent API: {base_url}")
    print("=" * 50)
    
    endpoints = [
        ("/", "Root Health Check"),
        ("/api/v1/health", "Detailed Health Check"),
        ("/api/v1/test", "Test Endpoint"),
        ("/api/v1/test/database", "Database Test"),
        ("/api/v1/movies", "Movies List"),
        ("/api/v1/movies/featured", "Featured Movies"),
        ("/api/v1/categories", "Categories"),
        ("/api/v1/languages", "Languages"),
    ]
    
    results = {}
    for endpoint, name in endpoints:
        success, data = test_endpoint(f"{base_url}{endpoint}", name)
        results[name] = {"success": success, "data": data}
    
    return results

def test_anime_data(base_url):
    """Test anime-specific data"""
    print(f"\n📺 Testing Anime Data")
    print("=" * 30)
    
    # Test movies endpoint for anime content
    success, data = test_endpoint(f"{base_url}/api/v1/movies?limit=5", "Anime Episodes")
    
    if success and data:
        movies = data.get("movies", [])
        print(f"  📊 Found {len(movies)} episodes")
        print(f"  📊 Total episodes in DB: {data.get('total', 0)}")
        
        if movies:
            sample_movie = movies[0]
            print(f"  🎬 Sample: {sample_movie.get('title', 'Unknown')}")
            print(f"  🎯 Difficulty: {sample_movie.get('difficulty_level', 'Unknown')}")
            print(f"  🌐 Languages: {sample_movie.get('languages', [])}")
    
    return success

def test_search_functionality(base_url):
    """Test search functionality"""
    print(f"\n🔍 Testing Search")
    print("=" * 20)
    
    search_terms = ["hero", "demon", "titan", "jujutsu"]
    
    for term in search_terms:
        success, data = test_endpoint(
            f"{base_url}/api/v1/movies/search?q={term}", 
            f"Search: '{term}'"
        )
        
        if success and data:
            count = len(data.get("movies", []))
            print(f"    Found {count} results for '{term}'")

def display_summary(results):
    """Display test summary"""
    print(f"\n📋 Test Summary")
    print("=" * 20)
    
    successful = sum(1 for r in results.values() if r["success"])
    total = len(results)
    
    print(f"✅ Successful: {successful}/{total}")
    
    if successful < total:
        print("\n❌ Failed Tests:")
        for name, result in results.items():
            if not result["success"]:
                print(f"  - {name}")
    
    print(f"\n🕒 Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

def main():
    """Main test function"""
    print("🎌 CineFluent API - Comprehensive Test Suite")
    print("=" * 60)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Test production API
    print("\n🌐 Testing Production API...")
    prod_results = test_api_health(API_BASE_URL)
    
    # Test anime data
    anime_success = test_anime_data(API_BASE_URL)
    
    # Test search
    test_search_functionality(API_BASE_URL)
    
    # Display results
    display_summary(prod_results)
    
    # Check if we should test local API
    print(f"\n💡 To test local API, run:")
    print(f"   python main.py")
    print(f"   # Then in another terminal:")
    print(f"   python test_api.py --local")
    
    return all(r["success"] for r in prod_results.values()) and anime_success

if __name__ == "__main__":
    import sys
    
    if "--local" in sys.argv:
        # Test local API
        print("🏠 Testing Local API...")
        results = test_api_health(LOCAL_URL)
        display_summary(results)
    else:
        # Test production API
        success = main()
        exit_code = 0 if success else 1
        sys.exit(exit_code)