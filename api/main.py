from fastapi import FastAPI, File, UploadFile, Form, HTTPException, BackgroundTasks
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import uuid
import subprocess
import asyncio
from pathlib import Path
import shutil
from typing import Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="DiffRhythm Music Generation API",
    description="Generate music from LRC files and style prompts using DiffRhythm",
    version="1.0.0"
)

# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure this properly for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configuration
BASE_DIR = Path("/app")
INPUT_DIR = BASE_DIR / "input"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Ensure directories exist
TEMP_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# Storage for generation status
generation_status = {}

@app.get("/")
async def root():
    return {
        "message": "DiffRhythm Music Generation API",
        "version": "1.0.0",
        "status": "running"
    }

@app.get("/models")
async def get_available_models():
    """Get list of available DiffRhythm models"""
    models = [
        {
            "id": "ASLP-lab/DiffRhythm-1_2",
            "name": "DiffRhythm v1.2",
            "description": "Latest version with improved quality and reduced repetition",
            "max_length": 95
        },
        {
            "id": "ASLP-lab/DiffRhythm-base", 
            "name": "DiffRhythm Base",
            "description": "Base model for 1m35s generation",
            "max_length": 95
        },
        {
            "id": "ASLP-lab/DiffRhythm-full",
            "name": "DiffRhythm Full", 
            "description": "Full model for 4m45s generation",
            "max_length": 285
        }
    ]
    return {"models": models}

@app.post("/generate-music")
async def generate_music(
    background_tasks: BackgroundTasks,
    lrc_file: UploadFile = File(..., description="LRC lyrics file"),
    ref_prompt: str = Form(..., description="Reference style prompt (e.g., 'pop ballad, emotional piano')"),
    audio_length: Optional[int] = Form(95, description="Audio length in seconds (95 or 285)"),
    model_id: Optional[str] = Form("ASLP-lab/DiffRhythm-1_2", description="Model to use for generation"),
    batch_infer_num: Optional[int] = Form(1, description="Number of songs to generate"),
    use_chunked: Optional[bool] = Form(True, description="Use chunked decoding for memory efficiency")
):
    """
    Generate music from LRC file and reference prompt
    """
    
    # Validate inputs
    if not lrc_file.filename.endswith('.lrc'):
        raise HTTPException(status_code=400, detail="File must be an LRC file")
    
    if audio_length not in [95, 285]:
        raise HTTPException(status_code=400, detail="Audio length must be 95 or 285 seconds")
    
    # Generate unique task ID
    task_id = str(uuid.uuid4())
    
    try:
        # Save uploaded LRC file
        lrc_filename = f"{task_id}_{lrc_file.filename}"
        lrc_path = TEMP_DIR / lrc_filename
        
        with open(lrc_path, "wb") as buffer:
            shutil.copyfileobj(lrc_file.file, buffer)
        
        logger.info(f"Saved LRC file: {lrc_path}")
        
        # Initialize status
        generation_status[task_id] = {
            "status": "queued",
            "created_at": datetime.now().isoformat(),
            "progress": 0,
            "message": "Task queued for processing"
        }
        
        # Start generation in background
        background_tasks.add_task(
            run_music_generation,
            task_id,
            str(lrc_path),
            ref_prompt,
            audio_length,
            model_id,
            batch_infer_num,
            use_chunked
        )
        
        return {
            "task_id": task_id,
            "status": "accepted",
            "message": "Music generation started",
            "estimated_time": "2-5 minutes depending on length and hardware"
        }
        
    except Exception as e:
        logger.error(f"Error starting generation: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to start generation: {str(e)}")

async def run_music_generation(
    task_id: str,
    lrc_path: str,
    ref_prompt: str,
    audio_length: int,
    model_id: str,
    batch_infer_num: int,
    use_chunked: bool
):
    """
    Run the music generation process
    """
    try:
        # Update status
        generation_status[task_id].update({
            "status": "processing",
            "progress": 10,
            "message": "Initializing model..."
        })
        
        # Create output directory for this task
        task_output_dir = OUTPUT_DIR / task_id
        task_output_dir.mkdir(exist_ok=True)
        
        # Build command
        cmd = [
            "python3", "infer/infer.py",
            "--lrc-path", lrc_path,
            "--ref-prompt", ref_prompt,
            "--audio-length", str(audio_length),
            "--repo-id", model_id,
            "--output-dir", str(task_output_dir),
            "--batch-infer-num", str(batch_infer_num)
        ]
        
        if use_chunked:
            cmd.append("--chunked")
        
        # Set environment variables
        env = os.environ.copy()
        env["PYTHONPATH"] = f"{env.get('PYTHONPATH', '')}:{BASE_DIR}"
        env["CUDA_VISIBLE_DEVICES"] = "0"
        
        logger.info(f"Running command: {' '.join(cmd)}")
        
        # Update status
        generation_status[task_id].update({
            "progress": 30,
            "message": "Generating music..."
        })
        
        # Run the generation process
        process = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=BASE_DIR,
            env=env,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        
        stdout, stderr = await process.communicate()
        
        if process.returncode == 0:
            # Find generated audio file
            output_files = list(task_output_dir.glob("*.wav"))
            if not output_files:
                output_files = list(task_output_dir.glob("*.mp3"))
            
            if output_files:
                output_file = output_files[0]
                generation_status[task_id].update({
                    "status": "completed",
                    "progress": 100,
                    "message": "Generation completed successfully",
                    "output_file": str(output_file.relative_to(BASE_DIR)),
                    "file_size": output_file.stat().st_size
                })
                logger.info(f"Generation completed: {output_file}")
            else:
                raise Exception("No output file found after generation")
        else:
            error_msg = stderr.decode() if stderr else "Unknown error"
            logger.error(f"Generation failed: {error_msg}")
            raise Exception(f"Generation process failed: {error_msg}")
            
    except Exception as e:
        logger.error(f"Generation error for task {task_id}: {str(e)}")
        generation_status[task_id].update({
            "status": "failed",
            "progress": 0,
            "message": f"Generation failed: {str(e)}"
        })
    finally:
        # Cleanup temp LRC file
        try:
            if os.path.exists(lrc_path):
                os.remove(lrc_path)
        except Exception as e:
            logger.warning(f"Failed to cleanup temp file {lrc_path}: {e}")

@app.get("/status/{task_id}")
async def get_generation_status(task_id: str):
    """
    Get the status of a music generation task
    """
    if task_id not in generation_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    return generation_status[task_id]

@app.get("/download/{task_id}")
async def download_generated_music(task_id: str):
    """
    Download the generated music file
    """
    if task_id not in generation_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    status = generation_status[task_id]
    
    if status["status"] != "completed":
        raise HTTPException(status_code=400, detail="Generation not completed")
    
    if "output_file" not in status:
        raise HTTPException(status_code=404, detail="Output file not found")
    
    file_path = BASE_DIR / status["output_file"]
    
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Generated file not found on disk")
    
    return FileResponse(
        path=str(file_path),
        filename=f"generated_music_{task_id}.wav",
        media_type="audio/wav"
    )

@app.delete("/cleanup/{task_id}")
async def cleanup_generation(task_id: str):
    """
    Clean up files and status for a completed generation
    """
    if task_id not in generation_status:
        raise HTTPException(status_code=404, detail="Task not found")
    
    # Remove output directory
    task_output_dir = OUTPUT_DIR / task_id
    if task_output_dir.exists():
        shutil.rmtree(task_output_dir)
    
    # Remove from status tracking
    del generation_status[task_id]
    
    return {"message": "Cleanup completed"}

@app.get("/health")
async def health_check():
    """
    Health check endpoint
    """
    # Check GPU availability
    try:
        result = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,memory.used,memory.total", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            timeout=5
        )
        gpu_available = result.returncode == 0
        gpu_info = result.stdout.strip() if gpu_available else None
    except:
        gpu_available = False
        gpu_info = None
    
    return {
        "status": "healthy",
        "gpu_available": gpu_available,
        "gpu_info": gpu_info,
        "active_generations": len([s for s in generation_status.values() if s["status"] == "processing"])
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 