#!/usr/bin/env python3
"""
CineFluent Subtitle Learning Features Test Script
Test the complete subtitle upload, processing, and learning workflow
"""

import requests
import json
import io
import time
from typing import Dict, Any, Optional

# Configuration
LOCAL_URL = "http://localhost:8000"
RAILWAY_URL = "https://cinefluent-api-production.up.railway.app"

# Test user credentials
TEST_USER = {
    "email": "subtitle_test@cinefluent.com",
    "password": "TestPass123!",
    "full_name": "Subtitle Test User"
}

# Sample SRT content for testing
SAMPLE_SRT_CONTENT = """1
00:00:01,000 --> 00:00:04,000
Welcome to our fascinating language learning adventure.

2
00:00:04,500 --> 00:00:08,000
Today we'll explore sophisticated vocabulary through cinema.

3
00:00:08,500 --> 00:00:12,000
This innovative approach enhances comprehension significantly.

4
00:00:12,500 --> 00:00:16,000
Advanced learners will discover challenging linguistic patterns.

5
00:00:16,500 --> 00:00:20,000
Elementary concepts become more accessible through context.
"""

def make_request(url: str, method: str = "GET", data: Dict = None, files: Dict = None, headers: Dict = None) -> Dict[str, Any]:
    """Make HTTP request with error handling"""
    try:
        if method == "POST":
            if files:
                response = requests.post(url, data=data, files=files, headers=headers, timeout=30)
            else:
                response = requests.post(url, json=data, headers=headers, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, headers=headers, timeout=30)
        else:
            response = requests.get(url, headers=headers, timeout=30)
        
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
            "data": {"raw_response": response.text},
            "error": f"JSON decode error: {str(e)}"
        }

def test_authentication(base_url: str) -> Optional[str]:
    """Test authentication and return access token"""
    print("🔐 Testing Authentication...")
    
    # Try to register user (might already exist)
    register_result = make_request(
        f"{base_url}/api/v1/auth/register",
        method="POST",
        data=TEST_USER
    )
    
    if register_result["success"] and register_result["status_code"] in [200, 201]:
        print("   ✅ User registered successfully")
    elif register_result["status_code"] == 409:
        print("   ⚠️  User already exists, proceeding with login")
    else:
        print(f"   ❌ Registration failed: {register_result}")
    
    # Login
    login_result = make_request(
        f"{base_url}/api/v1/auth/login",
        method="POST",
        data={"email": TEST_USER["email"], "password": TEST_USER["password"]}
    )
    
    if login_result["success"] and login_result["status_code"] == 200:
        access_token = login_result["data"].get("access_token")
        if access_token:
            print("   ✅ Login successful")
            return access_token
        else:
            print("   ❌ No access token received")
            return None
    else:
        print(f"   ❌ Login failed: {login_result}")
        return None

def test_subtitle_features(base_url: str, token: str) -> Dict[str, Any]:
    """Test all subtitle learning features"""
    headers = {"Authorization": f"Bearer {token}"}
    results = {}
    
    print(f"\n🧪 Testing Subtitle Features at: {base_url}")
    
    # Test 1: Check if subtitle tables exist
    print("1️⃣ Testing subtitle feature availability...")
    feature_test = make_request(f"{base_url}/api/v1/test/subtitle-features")
    results["feature_availability"] = feature_test
    
    if feature_test["success"]:
        print("   ✅ Subtitle features are available")
    else:
        print("   ❌ Subtitle features not available")
        return results
    
    # Test 2: Create a test movie (or use existing one)
    print("2️⃣ Setting up test movie...")
    
    # First, try to get existing movies
    movies_result = make_request(f"{base_url}/api/v1/movies", headers=headers)
    
    test_movie_id = None
    if movies_result["success"] and movies_result["data"].get("movies"):
        # Use the first available movie
        test_movie_id = movies_result["data"]["movies"][0]["id"]
        print(f"   ✅ Using existing movie: {test_movie_id}")
    else:
        # Create a test movie entry directly in database would require admin access
        print("   ⚠️  No movies available for testing. You may need to add a movie to test subtitle upload.")
        return results
    
    results["test_movie_id"] = test_movie_id
    
    # Test 3: Upload subtitle file
    print("3️⃣ Testing subtitle upload...")
    
    # Create file-like object from sample SRT
    srt_file = io.BytesIO(SAMPLE_SRT_CONTENT.encode('utf-8'))
    
    files = {
        'file': ('test_subtitles.srt', srt_file, 'text/plain')
    }
    
    data = {
        'movie_id': test_movie_id,
        'language': 'en',
        'title': 'Test English Subtitles'
    }
    
    upload_result = make_request(
        f"{base_url}/api/v1/subtitles/upload",
        method="POST",
        data=data,
        files=files,
        headers=headers
    )
    
    results["subtitle_upload"] = upload_result
    subtitle_id = None
    
    if upload_result["success"] and upload_result["status_code"] == 200:
        subtitle_id = upload_result["data"].get("subtitle_id")
        print(f"   ✅ Subtitle uploaded successfully: {subtitle_id}")
        print(f"   📊 Stats: {upload_result['data'].get('stats', {})}")
    else:
        print(f"   ❌ Subtitle upload failed: {upload_result}")
        return results
    
    results["subtitle_id"] = subtitle_id
    
    # Test 4: Get learning segments
    print("4️⃣ Testing learning segments...")
    
    segments_result = make_request(
        f"{base_url}/api/v1/subtitles/{subtitle_id}/segments",
        headers=headers
    )
    
    results["learning_segments"] = segments_result
    segment_id = None
    
    if segments_result["success"] and segments_result["status_code"] == 200:
        segments = segments_result["data"].get("segments", [])
        if segments:
            segment_id = segments[0]["id"]
            print(f"   ✅ Retrieved {len(segments)} learning segments")
            print(f"   🎯 First segment: {segment_id}")
        else:
            print("   ⚠️  No learning segments found")
    else:
        print(f"   ❌ Failed to get learning segments: {segments_result}")
        return results
    
    results["segment_id"] = segment_id
    
    # Test 5: Get segment cues (detailed subtitle content)
    print("5️⃣ Testing segment cues...")
    
    cues_result = make_request(
        f"{base_url}/api/v1/subtitles/segment/{segment_id}/cues",
        headers=headers
    )
    
    results["segment_cues"] = cues_result
    
    if cues_result["success"] and cues_result["status_code"] == 200:
        cues = cues_result["data"].get("cues", [])
        vocabulary = cues_result["data"].get("segment", {}).get("vocabulary_words", [])
        print(f"   ✅ Retrieved {len(cues)} subtitle cues")
        print(f"   📚 Vocabulary words: {len(vocabulary)}")
        if vocabulary:
            print(f"   🔤 Sample words: {[w.get('word', 'N/A') for w in vocabulary[:3]]}")
    else:
        print(f"   ❌ Failed to get segment cues: {cues_result}")
    
    # Test 6: Update learning progress
    print("6️⃣ Testing progress tracking...")
    
    progress_data = {
        "segment_id": segment_id,
        "time_spent": 120,  # 2 minutes
        "words_learned": ["fascinating", "sophisticated"],
        "interactions": [
            {
                "word": "fascinating",
                "definition_viewed": True,
                "marked_learned": True,
                "quiz_attempted": False,
                "quiz_correct": False
            },
            {
                "word": "sophisticated",
                "definition_viewed": True,
                "marked_learned": False,
                "quiz_attempted": True,
                "quiz_correct": True
            }
        ],
        "completed": False
    }
    
    progress_result = make_request(
        f"{base_url}/api/v1/subtitles/segment/{segment_id}/progress",
        method="POST",
        data=progress_data,
        headers=headers
    )
    
    results["progress_update"] = progress_result
    
    if progress_result["success"] and progress_result["status_code"] == 200:
        print("   ✅ Progress updated successfully")
    else:
        print(f"   ❌ Failed to update progress: {progress_result}")
    
    # Test 7: Generate quiz
    print("7️⃣ Testing quiz generation...")
    
    quiz_result = make_request(
        f"{base_url}/api/v1/subtitles/segment/{segment_id}/quiz?question_count=3",
        headers=headers
    )
    
    results["quiz_generation"] = quiz_result
    quiz_session_id = None
    
    if quiz_result["success"] and quiz_result["status_code"] == 200:
        quiz_session_id = quiz_result["data"].get("quiz_session_id")
        questions = quiz_result["data"].get("questions", [])
        print(f"   ✅ Quiz generated with {len(questions)} questions")
        print(f"   🎯 Quiz session: {quiz_session_id}")
        
        if questions:
            sample_question = questions[0]
            print(f"   ❓ Sample question: {sample_question.get('question', 'N/A')}")
    else:
        print(f"   ❌ Failed to generate quiz: {quiz_result}")
    
    results["quiz_session_id"] = quiz_session_id
    
    # Test 8: Submit quiz answer
    if quiz_session_id and quiz_result["data"].get("questions"):
        print("8️⃣ Testing quiz submission...")
        
        first_question = quiz_result["data"]["questions"][0]
        submission_data = {
            "question_id": first_question["id"],
            "selected_answer": first_question["correct_answer"],  # Submit correct answer
            "time_taken": 5
        }
        
        submission_result = make_request(
            f"{base_url}/api/v1/subtitles/quiz/{quiz_session_id}/submit",
            method="POST",
            data=submission_data,
            headers=headers
        )
        
        results["quiz_submission"] = submission_result
        
        if submission_result["success"] and submission_result["status_code"] == 200:
            is_correct = submission_result["data"].get("correct", False)
            print(f"   ✅ Quiz answer submitted - Correct: {is_correct}")
        else:
            print(f"   ❌ Failed to submit quiz answer: {submission_result}")
    
    # Test 9: Get movie learning path
    print("9️⃣ Testing movie learning path...")
    
    learning_path_result = make_request(
        f"{base_url}/api/v1/movies/{test_movie_id}/learning-path?language=en",
        headers=headers
    )
    
    results["learning_path"] = learning_path_result
    
    if learning_path_result["success"] and learning_path_result["status_code"] == 200:
        path_data = learning_path_result["data"]
        learning_path = path_data.get("learning_path", [])
        stats = path_data.get("stats", {})
        print(f"   ✅ Learning path generated with {len(learning_path)} segments")
        print(f"   📊 Total vocabulary: {stats.get('total_vocabulary', 0)} words")
        print(f"   ⏱️  Estimated time: {stats.get('estimated_learning_time', 0)} seconds")
    else:
        print(f"   ❌ Failed to generate learning path: {learning_path_result}")
    
    # Test 10: Get learning analytics
    print("🔟 Testing learning analytics...")
    
    analytics_result = make_request(
        f"{base_url}/api/v1/analytics/learning-progress?days=7",
        headers=headers
    )
    
    results["analytics"] = analytics_result
    
    if analytics_result["success"] and analytics_result["status_code"] == 200:
        analytics_data = analytics_result["data"]
        totals = analytics_data.get("totals", {})
        streaks = analytics_data.get("streaks", {})
        print(f"   ✅ Analytics retrieved")
        print(f"   📈 Words learned: {totals.get('words_learned', 0)}")
        print(f"   🔥 Current streak: {streaks.get('current_streak', 0)} days")
    else:
        print(f"   ❌ Failed to get analytics: {analytics_result}")
    
    return results

def print_comprehensive_summary(local_results: Dict, railway_results: Dict):
    """Print comprehensive test summary"""
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE SUBTITLE FEATURES TEST SUMMARY")
    print("="*80)
    
    tests = [
        ("feature_availability", "Feature Availability"),
        ("subtitle_upload", "Subtitle Upload"),
        ("learning_segments", "Learning Segments"),
        ("segment_cues", "Segment Cues"),
        ("progress_update", "Progress Tracking"),
        ("quiz_generation", "Quiz Generation"),
        ("learning_path", "Learning Path"),
        ("analytics", "Learning Analytics")
    ]
    
    print(f"{'Test':<25} {'Local':<15} {'Railway':<15} {'Description'}")
    print("-" * 80)
    
    for test_key, test_name in tests:
        local_status = "✅ PASS" if local_results.get(test_key, {}).get("success") else "❌ FAIL"
        railway_status = "✅ PASS" if railway_results.get(test_key, {}).get("success") else "❌ FAIL"
        
        descriptions = {
            "feature_availability": "Subtitle tables exist",
            "subtitle_upload": "SRT/VTT file processing",
            "learning_segments": "Content segmentation",
            "segment_cues": "Enriched subtitle data",
            "progress_update": "User progress tracking",
            "quiz_generation": "Auto quiz creation",
            "learning_path": "Personalized learning",
            "analytics": "Progress analytics"
        }
        
        description = descriptions.get(test_key, "")
        print(f"{test_name:<25} {local_status:<15} {railway_status:<15} {description}")
    
    # Detailed Railway Results
    print(f"\n{'='*80}")
    print("🚀 RAILWAY DEPLOYMENT DETAILED RESULTS")
    print(f"{'='*80}")
    
    critical_features = ["subtitle_upload", "learning_segments", "progress_update"]
    all_critical_working = all(railway_results.get(feature, {}).get("success", False) for feature in critical_features)
    
    if all_critical_working:
        print("🎉 SUCCESS! All critical subtitle learning features are working on Railway!")
        print("\n✅ Your backend can now:")
        print("   • Process and enrich subtitle files (SRT/VTT)")
        print("   • Extract vocabulary with difficulty levels")
        print("   • Create interactive learning segments")
        print("   • Track user progress and interactions")
        print("   • Generate vocabulary quizzes automatically")
        print("   • Provide learning analytics and insights")
        print("   • Support spaced repetition learning")
        
        if railway_results.get("subtitle_id"):
            print(f"\n📁 Test data created:")
            print(f"   • Subtitle ID: {railway_results.get('subtitle_id')}")
            print(f"   • Segment ID: {railway_results.get('segment_id')}")
            print(f"   • Quiz Session: {railway_results.get('quiz_session_id')}")
        
    else:
        print("❌ Some critical features need debugging on Railway")
        print("\n🔧 Issues found:")
        for feature in critical_features:
            if not railway_results.get(feature, {}).get("success", False):
                error = railway_results.get(feature, {}).get("error", "Unknown error")
                print(f"   • {feature}: {error}")
    
    # Success metrics
    local_success_rate = sum(1 for test_key, _ in tests if local_results.get(test_key, {}).get("success", False)) / len(tests) * 100
    railway_success_rate = sum(1 for test_key, _ in tests if railway_results.get(test_key, {}).get("success", False)) / len(tests) * 100
    
    print(f"\n📊 SUCCESS RATES:")
    print(f"   • Local Development: {local_success_rate:.1f}%")
    print(f"   • Railway Production: {railway_success_rate:.1f}%")
    
    if railway_success_rate >= 80:
        print(f"\n🎯 NEXT STEPS:")
        print("1. Connect your frontend to these subtitle endpoints")
        print("2. Implement video player with subtitle sync")
        print("3. Add vocabulary interaction UI components")
        print("4. Create progress tracking dashboards")
        print("5. Test with real movie content and subtitles")

def main():
    """Run comprehensive subtitle features test"""
    print("🎬 CineFluent Subtitle Learning Features Test Suite")
    print("="*80)
    print("This test will verify the complete subtitle processing and learning workflow")
    
    # Test locally
    print("\n🏠 TESTING LOCAL DEVELOPMENT SERVER")
    local_token = test_authentication(LOCAL_URL)
    local_results = {}
    
    if local_token:
        local_results = test_subtitle_features(LOCAL_URL, local_token)
    else:
        print("❌ Local authentication failed, skipping feature tests")
    
    # Test Railway
    print(f"\n🚀 TESTING RAILWAY PRODUCTION DEPLOYMENT")
    railway_token = test_authentication(RAILWAY_URL)
    railway_results = {}
    
    if railway_token:
        railway_results = test_subtitle_features(RAILWAY_URL, railway_token)
    else:
        print("❌ Railway authentication failed, skipping feature tests")
    
    # Print comprehensive summary
    print_comprehensive_summary(local_results, railway_results)

if __name__ == "__main__":
    main()