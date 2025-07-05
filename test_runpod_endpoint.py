#!/usr/bin/env python3
"""
Test script for deployed RunPod Serverless endpoint
Use this to test your endpoint after deployment
"""

import requests
import json
import base64
import time
from pathlib import Path

# Replace with your actual RunPod endpoint URL
RUNPOD_ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
# Your RunPod API key
RUNPOD_API_KEY = "YOUR_API_KEY"

def test_runpod_endpoint():
    """Test the deployed RunPod endpoint"""
    
    print("🚀 Testing RunPod Serverless Endpoint")
    print("=" * 50)
    
    # Read LRC file
    lrc_path = Path("input/vergil_of_sparda.lrc")  # Adjust path as needed
    
    if not lrc_path.exists():
        print(f"❌ LRC file not found: {lrc_path}")
        print("Please provide path to an LRC file")
        return False
    
    with open(lrc_path, 'r', encoding='utf-8') as f:
        lrc_content = f.read()
    
    # Prepare request payload
    payload = {
        "input": {
            "lrc_content": lrc_content,
            "ref_prompt": "hard rock, aggressive mood, electric guitar and drums",
            "audio_length": 95,
            "model_id": "ASLP-lab/DiffRhythm-1_2",
            "use_chunked": True
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("📝 Request details:")
    print(f"   Endpoint: {RUNPOD_ENDPOINT_URL}")
    print(f"   LRC length: {len(lrc_content)} characters")
    print(f"   Prompt: {payload['input']['ref_prompt']}")
    print(f"   Audio length: {payload['input']['audio_length']}s")
    
    try:
        print("\n🔄 Sending request to RunPod...")
        start_time = time.time()
        
        response = requests.post(
            RUNPOD_ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=600  # 10 minute timeout
        )
        
        total_time = time.time() - start_time
        
        print(f"📡 Response received in {total_time:.2f}s")
        print(f"   Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            
            if result.get("status") == "COMPLETED":
                output = result.get("output", {})
                
                if output.get("success"):
                    print("✅ Generation successful!")
                    print(f"   Generation time: {output.get('generation_time', 0):.2f}s")
                    print(f"   File size: {output.get('file_size', 0)} bytes")
                    print(f"   Model used: {output.get('model_used', 'Unknown')}")
                    
                    # Save generated audio
                    if output.get('audio_base64'):
                        audio_data = base64.b64decode(output['audio_base64'])
                        output_path = Path("generated_music_runpod.wav")
                        
                        with open(output_path, 'wb') as f:
                            f.write(audio_data)
                        
                        print(f"🎵 Audio saved: {output_path}")
                        print(f"   File size: {len(audio_data)} bytes")
                        
                    return True
                else:
                    print("❌ Generation failed!")
                    print(f"   Error: {output.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Request failed with status: {result.get('status')}")
                if 'error' in result:
                    print(f"   Error: {result['error']}")
                return False
        else:
            print(f"❌ HTTP Error {response.status_code}")
            print(f"   Response: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("⏰ Request timed out (>10 minutes)")
        return False
    except Exception as e:
        print(f"❌ Request failed: {str(e)}")
        return False

def test_with_custom_input():
    """Test with custom LRC content and prompt"""
    
    custom_lrc = """[00:00.00]Test song intro
[00:05.00]This is a test
[00:10.00]For music generation
[00:15.00]Using DiffRhythm model"""
    
    payload = {
        "input": {
            "lrc_content": custom_lrc,
            "ref_prompt": "electronic pop, synthesizer, upbeat tempo",
            "audio_length": 95,
            "use_chunked": True
        }
    }
    
    headers = {
        "Authorization": f"Bearer {RUNPOD_API_KEY}",
        "Content-Type": "application/json"
    }
    
    print("\n🎵 Testing with custom input...")
    print(f"   Custom prompt: {payload['input']['ref_prompt']}")
    
    try:
        response = requests.post(
            RUNPOD_ENDPOINT_URL,
            headers=headers,
            json=payload,
            timeout=600
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get("status") == "COMPLETED" and result.get("output", {}).get("success"):
                print("✅ Custom input test passed!")
                return True
        
        print("❌ Custom input test failed")
        return False
        
    except Exception as e:
        print(f"❌ Custom input test error: {str(e)}")
        return False

if __name__ == "__main__":
    # Check if endpoint URL and API key are set
    if "YOUR_ENDPOINT_ID" in RUNPOD_ENDPOINT_URL or "YOUR_API_KEY" in RUNPOD_API_KEY:
        print("❌ Please update RUNPOD_ENDPOINT_URL and RUNPOD_API_KEY in this script")
        print("   Get these from your RunPod dashboard after deployment")
        exit(1)
    
    # Run tests
    success1 = test_runpod_endpoint()
    success2 = test_with_custom_input()
    
    print("\n" + "=" * 50)
    print("📊 Test Summary:")
    if success1 and success2:
        print("🎉 All tests passed! Your RunPod endpoint is working correctly.")
    else:
        print("⚠️  Some tests failed. Check the logs above for details.") 