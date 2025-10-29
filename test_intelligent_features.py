"""
Test script for the new Intelligent Authoring Assistant features
"""

import requests
import json

# Test configuration
API_BASE_URL = "http://localhost:8000"  # Change to Render URL when deployed
# API_BASE_URL = "https://ilanalabs-add-in.onrender.com"

def test_intelligent_suggestions():
    """Test the intelligent suggestions endpoint"""
    print("🧠 Testing Intelligent Suggestions...")
    
    test_text = """
    Patients will be monitored as needed with frequent monitoring. 
    The drug is safe and proven effective. Daily visits are required 
    for extensive testing to ensure patient safety.
    """
    
    payload = {
        "text": test_text,
        "context": "general"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/intelligent-suggestions", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Intelligent Suggestions Test PASSED")
            print(f"   - Found {len(result['phrase_suggestions'])} phrase suggestions")
            print(f"   - Found {len(result['feasibility_concerns'])} feasibility concerns")
            print(f"   - Found {len(result['regulatory_flags'])} regulatory flags")
            
            # Print some examples
            if result['phrase_suggestions']:
                print(f"   - Example suggestion: '{result['phrase_suggestions'][0]['original']}' → '{result['phrase_suggestions'][0]['suggestions'][0]}'")
            
            return True
        else:
            print(f"❌ Intelligent Suggestions Test FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Intelligent Suggestions Test FAILED: {e}")
        return False

def test_comment_categorization():
    """Test the comment categorization endpoint"""
    print("\n📝 Testing Comment Categorization...")
    
    test_comments = [
        "Please clarify what is meant by 'as needed' dosing",
        "The proposed visit schedule seems too frequent for most sites",
        "This endpoint definition doesn't align with FDA guidance",
        "Statistical power calculation needs revision"
    ]
    
    for i, comment in enumerate(test_comments):
        try:
            payload = {"comment_text": comment}
            response = requests.post(f"{API_BASE_URL}/api/categorize-comment", 
                                   json=payload, timeout=30)
            
            if response.status_code == 200:
                result = response.json()
                print(f"✅ Comment {i+1}: Category = {result['category']}, Confidence = {result['confidence']}")
            else:
                print(f"❌ Comment {i+1} categorization failed: HTTP {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Comment {i+1} categorization failed: {e}")
            return False
    
    print("✅ Comment Categorization Test PASSED")
    return True

def test_feasibility_check():
    """Test the feasibility check endpoint"""
    print("\n⚡ Testing Feasibility Check...")
    
    test_text = """
    This study requires daily visits for the first month, with extensive 
    testing including multiple biopsies and specialized equipment. 
    Participants need continuous monitoring with certified technicians.
    """
    
    payload = {"text": test_text}
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/feasibility-check", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Feasibility Check Test PASSED")
            print(f"   - Found {len(result['concerns'])} feasibility concerns")
            
            for concern in result['concerns']:
                print(f"   - {concern['type']}: {concern['concern']}")
            
            return True
        else:
            print(f"❌ Feasibility Check Test FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Feasibility Check Test FAILED: {e}")
        return False

def test_phrase_suggestions():
    """Test the phrase suggestions endpoint"""
    print("\n💡 Testing Phrase Suggestions...")
    
    test_text = "Patients will receive medication as needed for symptom improvement"
    
    payload = {
        "text": test_text,
        "context": "dosing"
    }
    
    try:
        response = requests.post(f"{API_BASE_URL}/api/phrase-suggestions", 
                               json=payload, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Phrase Suggestions Test PASSED")
            print(f"   - Found {len(result['suggestions'])} phrase suggestions")
            
            for suggestion in result['suggestions']:
                print(f"   - '{suggestion['original']}' ({suggestion['category']}, {suggestion['severity']})")
            
            return True
        else:
            print(f"❌ Phrase Suggestions Test FAILED: HTTP {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Phrase Suggestions Test FAILED: {e}")
        return False

def main():
    """Run all tests"""
    print("🚀 TESTING INTELLIGENT AUTHORING ASSISTANT FEATURES")
    print("=" * 60)
    
    tests = [
        test_intelligent_suggestions,
        test_comment_categorization,
        test_feasibility_check,
        test_phrase_suggestions
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        if test():
            passed += 1
    
    print(f"\n{'=' * 60}")
    print(f"🎯 TEST SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! Intelligent features are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the API deployment and database.")

if __name__ == "__main__":
    main()