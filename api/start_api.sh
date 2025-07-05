#!/bin/bash

# Navigate to the app directory
cd /app

# Set environment variables
export PYTHONPATH=$PYTHONPATH:/app
export CUDA_VISIBLE_DEVICES=0

# Start the FastAPI server
echo "Starting DiffRhythm API server..."
python3 api/main.py 