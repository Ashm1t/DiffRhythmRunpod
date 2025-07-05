#!/usr/bin/env python3
"""
RunPod Serverless Handler for DiffRhythm Music Generation
This handler processes music generation requests in RunPod's serverless environment
"""

import runpod
import os
import tempfile
import subprocess
import base64
import json
import time
from pathlib import Path
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Set environment variables
os.environ["CUDA_VISIBLE_DEVICES"] = "0"
os.environ["PYTHONPATH"] = "/app"

def initialize_model():
    """
    Initialize the DiffRhythm model (called once on cold start)
    """
    logger.info("🔥 Initializing DiffRhythm model...")
    
    # Pre-load models if needed (optional optimization)
    # This can reduce inference time by pre-loading models into memory
    
    logger.info("✅ Model initialization completed")
    return True

def generate_music(lrc_content: str, ref_prompt: str, audio_length: int = 95, 
                  model_id: str = "ASLP-lab/DiffRhythm-1_2", 
                  use_chunked: bool = True) -> Dict[str, Any]:
    """
    Generate music using DiffRhythm model
    
    Args:
        lrc_content: LRC file content as string
        ref_prompt: Style prompt for music generation
        audio_length: Length in seconds (95 or 285)
        model_id: Model to use for generation
        use_chunked: Whether to use chunked decoding
    
    Returns:
        Dictionary with generated audio data and metadata
    """
    
    logger.info(f"🎵 Starting music generation with prompt: '{ref_prompt}'")
    
    # Create temporary directories
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        lrc_path = temp_path / "input.lrc"
        output_dir = temp_path / "output"
        output_dir.mkdir(exist_ok=True)
        
        # Save LRC content to file
        with open(lrc_path, 'w', encoding='utf-8') as f:
            f.write(lrc_content)
        
        logger.info(f"📝 Saved LRC file: {lrc_path}")
        
        # Build command
        cmd = [
            "python3", "/app/infer/infer.py",
            "--lrc-path", str(lrc_path),
            "--ref-prompt", ref_prompt,
            "--audio-length", str(audio_length),
            "--repo-id", model_id,
            "--output-dir", str(output_dir),
            "--batch-infer-num", "1"
        ]
        
        if use_chunked:
            cmd.append("--chunked")
        
        logger.info(f"🔧 Running command: {' '.join(cmd)}")
        
        # Run generation
        start_time = time.time()
        try:
            result = subprocess.run(
                cmd,
                cwd="/app",
                capture_output=True,
                text=True,
                timeout=600  # 10 minute timeout
            )
            
            generation_time = time.time() - start_time
            
            if result.returncode == 0:
                # Find generated audio file
                output_files = list(output_dir.glob("*.wav"))
                if not output_files:
                    output_files = list(output_dir.glob("*.mp3"))
                
                if output_files:
                    output_file = output_files[0]
                    file_size = output_file.stat().st_size
                    
                    logger.info(f"✅ Generation completed in {generation_time:.2f}s")
                    logger.info(f"📁 Output file: {output_file} ({file_size} bytes)")
                    
                    # Read audio file and encode as base64
                    with open(output_file, 'rb') as f:
                        audio_data = f.read()
                        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
                    
                    return {
                        "success": True,
                        "audio_base64": audio_base64,
                        "file_size": file_size,
                        "generation_time": generation_time,
                        "audio_length": audio_length,
                        "model_used": model_id,
                        "prompt": ref_prompt,
                        "message": "Music generation completed successfully"
                    }
                else:
                    raise Exception("No output file generated")
            else:
                error_msg = result.stderr or result.stdout or "Unknown error"
                logger.error(f"❌ Generation failed: {error_msg}")
                raise Exception(f"Generation failed: {error_msg}")
                
        except subprocess.TimeoutExpired:
            logger.error("❌ Generation timed out after 10 minutes")
            raise Exception("Generation timed out")
        except Exception as e:
            logger.error(f"❌ Generation error: {str(e)}")
            raise e

def handler(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    RunPod Serverless handler function
    
    Expected input format:
    {
        "input": {
            "lrc_content": "LRC file content as string",
            "ref_prompt": "Style description",
            "audio_length": 95,  # optional
            "model_id": "ASLP-lab/DiffRhythm-1_2",  # optional
            "use_chunked": true  # optional
        }
    }
    """
    
    try:
        logger.info("🚀 RunPod handler started")
        
        # Extract input data
        input_data = event.get('input', {})
        
        # Required parameters
        lrc_content = input_data.get('lrc_content')
        ref_prompt = input_data.get('ref_prompt')
        
        if not lrc_content:
            return {
                "error": "Missing required parameter: lrc_content",
                "success": False
            }
        
        if not ref_prompt:
            return {
                "error": "Missing required parameter: ref_prompt", 
                "success": False
            }
        
        # Optional parameters with defaults
        audio_length = input_data.get('audio_length', 95)
        model_id = input_data.get('model_id', 'ASLP-lab/DiffRhythm-1_2')
        use_chunked = input_data.get('use_chunked', True)
        
        # Validate audio length
        if audio_length not in [95, 285]:
            return {
                "error": "audio_length must be 95 or 285 seconds",
                "success": False
            }
        
        logger.info(f"📝 Processing request: {len(lrc_content)} chars LRC, prompt: '{ref_prompt}', length: {audio_length}s")
        
        # Generate music
        result = generate_music(
            lrc_content=lrc_content,
            ref_prompt=ref_prompt,
            audio_length=audio_length,
            model_id=model_id,
            use_chunked=use_chunked
        )
        
        logger.info("🎉 Handler completed successfully")
        return result
        
    except Exception as e:
        logger.error(f"❌ Handler error: {str(e)}")
        return {
            "error": str(e),
            "success": False
        }

if __name__ == "__main__":
    # Initialize model on startup
    initialize_model()
    
    # Start RunPod serverless
    logger.info("🔥 Starting RunPod Serverless handler...")
    runpod.serverless.start({"handler": handler}) 