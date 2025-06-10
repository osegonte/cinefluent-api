#!/usr/bin/env python3
"""
CineFluent - Simple API Test (No External Dependencies)
Test the API using only built-in Python modules
"""

import urllib.request
import urllib.error
import json
from datetime import datetime

def test_api_endpoint(url, name):
    """Test a single API endpoint using urllib"""
    try:
        print(f"  Testing {name}...")
        
        with urllib.request.urlopen(url, timeout=10) as response:
            if response.status == 200:
                data = json.loads(response.read().decode('utf-8'))
                print(f"  ✅ {name} - OK")
                return True, data
            else:
                print(f"  ❌ {name} - Status: {response.status}")
                return False, None
                
    except urllib.error.URLError as e:
        print(f"  ❌ {name} - Error: {e}")
        return False, None
    except Exception as e:
        print(f"  ❌ {name} - Unexpected error: {e}")
        return False, None

def main():
    """Test CineFluent API endpoints"""
    print("🎌 CineFluent API - Simple Test")
    print("=" * 40)
    print(f"🕒 Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    base_url = "https://cinefluent-api-production.up.railway.app"
    
    # Test endpoints
    endpoints = [
        ("/", "Root Health Check"),
        ("/api/v1/health", "Detailed Health"),
        ("/api/v1/test", "Test Endpoint"),
        ("/api/v1/movies", "Anime Episodes"),
        ("/api/v1/movies/featured", "Featured Episodes"),
        ("/api/v1/categories", "Categories"),
        ("/api/v1/languages", "Languages"),
    ]
    
    results = {}
    
    for endpoint, name in endpoints:
        success, data = test_api_endpoint(f"{base_url}{endpoint}", name)
        results[name] = success
        
        # Show some data for key endpoints
        if success and data:
            if name == "Anime Episodes":
                total = data.get("total", 0)
                movies = data.get("movies", [])
                print(f"    📺 Total episodes: {total}")
                print(f"    📄 Returned: {len(movies)} episodes")
                
            elif name == "Featured Episodes":
                movies = data.get("movies", [])
                print(f"    ⭐ Featured episodes: {len(movies)}")
                
            elif name == "Detailed Health":
                status = data.get("status", "unknown")
                env = data.get("environment", {}).get("railway_env", "unknown")
                print(f"    🏥 Status: {status}")
                print(f"    🌍 Environment: {env}")
    
    # Summary
    print(f"\n📋 Test Summary:")
    successful = sum(1 for success in results.values() if success)
    total = len(results)
    print(f"✅ Successful: {successful}/{total}")
    
    if successful < total:
        print(f"\n❌ Failed tests:")
        for name, success in results.items():
            if not success:
                print(f"  - {name}")
    
    # Next steps
    if successful >= 4:  # Most important endpoints working
        print(f"\n🎉 Your CineFluent API is working!")
        print(f"🎯 Next steps:")
        print(f"   1. Set up virtual environment: chmod +x setup_virtual_environment.sh && ./setup_virtual_environment.sh")
        print(f"   2. Test with full features: python test_api.py")
        print(f"   3. Start local development: python main.py")
    else:
        print(f"\n⚠️  Some endpoints are not responding. Check your deployment.")
    
    print(f"\n🕒 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return successful >= 4

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)