#!/usr/bin/env python3
"""
Local test script for RunPod handler
Tests the handler function before deploying to RunPod Serverless
"""

import json
import base64
from runpod_handler import handler
from pathlib import Path

def test_handler_locally():
    """Test the RunPod handler function locally"""
    
    print("🧪 Testing RunPod handler locally...")
    
    # Read the Vergil LRC file
    lrc_path = Path("/app/input/vergil_of_sparda.lrc")
    
    if not lrc_path.exists():
        print(f"❌ LRC file not found: {lrc_path}")
        return False
    
    with open(lrc_path, 'r', encoding='utf-8') as f:
        lrc_content = f.read()
    
    # Create test event (RunPod format)
    test_event = {
        "input": {
            "lrc_content": lrc_content,
            "ref_prompt": "hard rock, aggressive mood, electric guitar and drums",
            "audio_length": 95,
            "model_id": "ASLP-lab/DiffRhythm-1_2",
            "use_chunked": True
        }
    }
    
    print("📝 Test input:")
    print(f"   LRC length: {len(lrc_content)} characters")
    print(f"   Prompt: {test_event['input']['ref_prompt']}")
    print(f"   Audio length: {test_event['input']['audio_length']}s")
    
    try:
        # Call the handler
        print("\n🚀 Calling handler...")
        result = handler(test_event)
        
        if result.get("success"):
            print("✅ Handler test PASSED!")
            print(f"   Generation time: {result.get('generation_time', 0):.2f}s")
            print(f"   File size: {result.get('file_size', 0)} bytes")
            print(f"   Audio data: {len(result.get('audio_base64', ''))} base64 chars")
            
            # Save the generated audio for testing
            if result.get('audio_base64'):
                audio_data = base64.b64decode(result['audio_base64'])
                output_path = Path("/app/test_output.wav")
                with open(output_path, 'wb') as f:
                    f.write(audio_data)
                print(f"   Test output saved: {output_path}")
            
            return True
        else:
            print("❌ Handler test FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            return False
            
    except Exception as e:
        print(f"❌ Handler test FAILED with exception: {str(e)}")
        return False

def test_error_cases():
    """Test error handling"""
    
    print("\n🔍 Testing error cases...")
    
    # Test missing LRC content
    result1 = handler({"input": {"ref_prompt": "test"}})
    assert not result1["success"], "Should fail without LRC content"
    print("✅ Missing LRC content handled correctly")
    
    # Test missing prompt
    result2 = handler({"input": {"lrc_content": "test"}})
    assert not result2["success"], "Should fail without prompt"
    print("✅ Missing prompt handled correctly")
    
    # Test invalid audio length
    result3 = handler({
        "input": {
            "lrc_content": "[00:00.00]Test",
            "ref_prompt": "test",
            "audio_length": 999
        }
    })
    assert not result3["success"], "Should fail with invalid audio length"
    print("✅ Invalid audio length handled correctly")

if __name__ == "__main__":
    print("🎵 DiffRhythm RunPod Handler Local Test")
    print("=" * 50)
    
    # Test error cases first (fast)
    test_error_cases()
    
    # Test full generation (slow)
    success = test_handler_locally()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All tests passed! Handler is ready for RunPod deployment.")
    else:
        print("⚠️  Tests failed. Fix issues before deploying to RunPod.") 