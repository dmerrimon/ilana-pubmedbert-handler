"""
Test HuggingFace endpoint availability
"""
import requests
import os
import time

def test_endpoint():
    url = "https://usz78oxlybv4xfh2.eastus.azure.endpoints.huggingface.cloud"
    api_key = os.getenv("HUGGINGFACE_API_KEY")
    
    headers = {"Authorization": f"Bearer {api_key}"}
    
    print(f"Testing endpoint: {url}")
    print("Sending test request...")
    
    start_time = time.time()
    try:
        response = requests.post(
            url,
            headers=headers,
            json={"inputs": "test clinical protocol"},
            timeout=60
        )
        end_time = time.time()
        
        print(f"Response time: {end_time - start_time:.2f} seconds")
        print(f"Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Endpoint is working!")
            print(f"Response keys: {result.keys() if isinstance(result, dict) else 'Not a dict'}")
        else:
            print(f"❌ Error: {response.status_code} - {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Request timed out after 60 seconds")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_endpoint()