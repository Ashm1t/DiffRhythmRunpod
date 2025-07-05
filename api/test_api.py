#!/usr/bin/env python3
"""
Test script for DiffRhythm API
Demonstrates how to interact with the music generation endpoints
"""

import requests
import time
import json
from pathlib import Path

API_BASE_URL = "http://localhost:8000"

def test_health_check():
    """Test the health endpoint"""
    print("🏥 Testing health check...")
    response = requests.get(f"{API_BASE_URL}/health")
    if response.status_code == 200:
        health_data = response.json()
        print(f"✅ API is healthy")
        print(f"   GPU Available: {health_data.get('gpu_available', False)}")
        print(f"   Active Generations: {health_data.get('active_generations', 0)}")
        return True
    else:
        print(f"❌ Health check failed: {response.status_code}")
        return False

def test_models_endpoint():
    """Test the models endpoint"""
    print("\n🤖 Testing models endpoint...")
    response = requests.get(f"{API_BASE_URL}/models")
    if response.status_code == 200:
        models = response.json()
        print("✅ Available models:")
        for model in models['models']:
            print(f"   - {model['name']}: {model['id']} (max: {model['max_length']}s)")
        return True
    else:
        print(f"❌ Models endpoint failed: {response.status_code}")
        return False

def test_music_generation():
    """Test music generation with the Vergil LRC file"""
    print("\n🎵 Testing music generation...")
    
    # Use the existing Vergil LRC file
    lrc_file_path = Path("/app/input/vergil_of_sparda.lrc")
    
    if not lrc_file_path.exists():
        print(f"❌ LRC file not found: {lrc_file_path}")
        return False
    
    # Prepare the request
    files = {
        'lrc_file': ('vergil_of_sparda.lrc', open(lrc_file_path, 'rb'), 'text/plain')
    }
    
    data = {
        'ref_prompt': 'hard rock, aggressive mood, electric guitar and drums',
        'audio_length': 95,
        'model_id': 'ASLP-lab/DiffRhythm-1_2',
        'batch_infer_num': 1,
        'use_chunked': True
    }
    
    try:
        # Start generation
        print("   Starting generation...")
        response = requests.post(f"{API_BASE_URL}/generate-music", files=files, data=data)
        
        if response.status_code != 200:
            print(f"❌ Generation request failed: {response.status_code}")
            print(response.text)
            return False
        
        result = response.json()
        task_id = result['task_id']
        print(f"✅ Generation started with task ID: {task_id}")
        
        # Poll for status (but don't wait for completion in test)
        print("   Checking initial status...")
        status_response = requests.get(f"{API_BASE_URL}/status/{task_id}")
        
        if status_response.status_code == 200:
            status = status_response.json()
            print(f"   Status: {status['status']}")
            print(f"   Progress: {status['progress']}%")
            print(f"   Message: {status['message']}")
            
            print("\n💡 To monitor progress, use:")
            print(f"   curl {API_BASE_URL}/status/{task_id}")
            print("\n💡 To download when complete, use:")
            print(f"   curl -O {API_BASE_URL}/download/{task_id}")
            
            return True
        else:
            print(f"❌ Status check failed: {status_response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Generation test failed: {str(e)}")
        return False
    finally:
        files['lrc_file'][1].close()

def main():
    """Run all tests"""
    print("🚀 Testing DiffRhythm API")
    print("=" * 50)
    
    # Test basic connectivity
    try:
        response = requests.get(f"{API_BASE_URL}/", timeout=5)
        if response.status_code != 200:
            print(f"❌ API not responding: {response.status_code}")
            print("   Make sure the API server is running with: ./api/start_api.sh")
            return
    except requests.exceptions.RequestException as e:
        print(f"❌ Cannot connect to API: {str(e)}")
        print("   Make sure the API server is running with: ./api/start_api.sh")
        return
    
    print("✅ API is responding")
    
    # Run tests
    tests = [
        test_health_check,
        test_models_endpoint,
        test_music_generation
    ]
    
    results = []
    for test in tests:
        try:
            results.append(test())
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {str(e)}")
            results.append(False)
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    passed = sum(results)
    total = len(results)
    print(f"   Passed: {passed}/{total}")
    
    if all(results):
        print("🎉 All tests passed! API is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    main() 