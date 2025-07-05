# DiffRhythm Music Generation API

A FastAPI-based web service for generating music using the DiffRhythm model. This API accepts LRC (lyrics) files and style prompts to generate full-length songs.

## Features

- ✅ Upload LRC files and generate music with style prompts
- ✅ Asynchronous generation with status tracking
- ✅ Multiple model support (v1.2, base, full)
- ✅ Configurable audio length (95s or 285s)
- ✅ GPU health monitoring
- ✅ CORS enabled for frontend integration
- ✅ File cleanup and management

## Quick Start

### Start the API Server

```bash
# From the /app directory
./api/start_api.sh
```

The API will be available at `http://localhost:8000`

### API Documentation

Once running, visit:
- Interactive docs: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## API Endpoints

### `POST /generate-music`
Generate music from LRC file and style prompt.

**Parameters:**
- `lrc_file` (file): LRC lyrics file
- `ref_prompt` (string): Style prompt (e.g., "pop ballad, emotional piano")
- `audio_length` (int, optional): 95 or 285 seconds (default: 95)
- `model_id` (string, optional): Model to use (default: "ASLP-lab/DiffRhythm-1_2")
- `batch_infer_num` (int, optional): Number of songs to generate (default: 1)
- `use_chunked` (bool, optional): Use chunked decoding (default: true)

**Response:**
```json
{
  "task_id": "uuid-string",
  "status": "accepted",
  "message": "Music generation started",
  "estimated_time": "2-5 minutes depending on length and hardware"
}
```

### `GET /status/{task_id}`
Get generation status.

**Response:**
```json
{
  "status": "processing|completed|failed",
  "progress": 75,
  "message": "Generation in progress...",
  "created_at": "2025-01-01T12:00:00",
  "output_file": "output/task-id/generated.wav",
  "file_size": 1234567
}
```

### `GET /download/{task_id}`
Download the generated music file.

### `GET /models`
Get available models.

### `GET /health`
Health check and GPU status.

## Frontend Integration Examples

### JavaScript/Fetch Example

```javascript
// Upload LRC and generate music
async function generateMusic(lrcFile, stylePrompt) {
    const formData = new FormData();
    formData.append('lrc_file', lrcFile);
    formData.append('ref_prompt', stylePrompt);
    formData.append('audio_length', 95);
    formData.append('model_id', 'ASLP-lab/DiffRhythm-1_2');
    
    try {
        const response = await fetch('http://localhost:8000/generate-music', {
            method: 'POST',
            body: formData
        });
        
        const result = await response.json();
        console.log('Generation started:', result);
        
        // Poll for status
        await pollGenerationStatus(result.task_id);
        
    } catch (error) {
        console.error('Error:', error);
    }
}

// Poll generation status
async function pollGenerationStatus(taskId) {
    const interval = setInterval(async () => {
        try {
            const response = await fetch(`http://localhost:8000/status/${taskId}`);
            const status = await response.json();
            
            console.log('Status:', status);
            updateProgressUI(status.progress, status.message);
            
            if (status.status === 'completed') {
                clearInterval(interval);
                downloadMusic(taskId);
            } else if (status.status === 'failed') {
                clearInterval(interval);
                console.error('Generation failed:', status.message);
            }
        } catch (error) {
            console.error('Status check error:', error);
        }
    }, 2000); // Check every 2 seconds
}

// Download generated music
async function downloadMusic(taskId) {
    const downloadUrl = `http://localhost:8000/download/${taskId}`;
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = `generated_music_${taskId}.wav`;
    link.click();
}

// Update progress UI
function updateProgressUI(progress, message) {
    const progressBar = document.getElementById('progress-bar');
    const statusMessage = document.getElementById('status-message');
    
    if (progressBar) progressBar.value = progress;
    if (statusMessage) statusMessage.textContent = message;
}
```

### React Example

```jsx
import React, { useState, useCallback } from 'react';

const MusicGenerator = () => {
    const [file, setFile] = useState(null);
    const [prompt, setPrompt] = useState('');
    const [status, setStatus] = useState(null);
    const [progress, setProgress] = useState(0);
    
    const handleFileChange = (e) => {
        setFile(e.target.files[0]);
    };
    
    const generateMusic = async () => {
        if (!file || !prompt) return;
        
        const formData = new FormData();
        formData.append('lrc_file', file);
        formData.append('ref_prompt', prompt);
        formData.append('audio_length', 95);
        
        try {
            const response = await fetch('http://localhost:8000/generate-music', {
                method: 'POST',
                body: formData
            });
            
            const result = await response.json();
            setStatus(result);
            
            // Start polling
            pollStatus(result.task_id);
            
        } catch (error) {
            console.error('Error:', error);
        }
    };
    
    const pollStatus = (taskId) => {
        const interval = setInterval(async () => {
            try {
                const response = await fetch(`http://localhost:8000/status/${taskId}`);
                const statusData = await response.json();
                
                setProgress(statusData.progress);
                setStatus(statusData);
                
                if (statusData.status === 'completed' || statusData.status === 'failed') {
                    clearInterval(interval);
                }
            } catch (error) {
                console.error('Status error:', error);
            }
        }, 2000);
    };
    
    return (
        <div className="music-generator">
            <h2>Generate Music</h2>
            
            <div className="upload-section">
                <label>
                    LRC File:
                    <input 
                        type="file" 
                        accept=".lrc"
                        onChange={handleFileChange}
                    />
                </label>
            </div>
            
            <div className="prompt-section">
                <label>
                    Style Prompt:
                    <input 
                        type="text"
                        value={prompt}
                        onChange={(e) => setPrompt(e.target.value)}
                        placeholder="e.g., pop ballad, emotional piano"
                    />
                </label>
            </div>
            
            <button onClick={generateMusic} disabled={!file || !prompt}>
                Generate Music
            </button>
            
            {status && (
                <div className="status-section">
                    <p>Status: {status.status}</p>
                    <p>Message: {status.message}</p>
                    <progress value={progress} max="100">{progress}%</progress>
                    
                    {status.status === 'completed' && (
                        <a 
                            href={`http://localhost:8000/download/${status.task_id}`}
                            download
                        >
                            Download Music
                        </a>
                    )}
                </div>
            )}
        </div>
    );
};

export default MusicGenerator;
```

### cURL Examples

```bash
# Generate music
curl -X POST "http://localhost:8000/generate-music" \
     -F "lrc_file=@example.lrc" \
     -F "ref_prompt=pop ballad, emotional piano" \
     -F "audio_length=95" \
     -F "model_id=ASLP-lab/DiffRhythm-1_2"

# Check status
curl "http://localhost:8000/status/YOUR_TASK_ID"

# Download result
curl -O "http://localhost:8000/download/YOUR_TASK_ID"

# Get available models
curl "http://localhost:8000/models"

# Health check
curl "http://localhost:8000/health"
```

## Style Prompt Examples

### Good style prompts:
- `"pop ballad, emotional piano, soft vocals"`
- `"rock anthem, electric guitar, driving drums"`
- `"jazz fusion, saxophone, upright bass"`
- `"electronic dance, synthesizer, heavy bass"`
- `"acoustic folk, guitar fingerpicking, harmonica"`
- `"orchestral cinematic, strings, epic crescendo"`

### For your app's use cases:
- `"hard rock, aggressive mood, electric guitar and drums"` (like Vergil theme)
- `"ambient electronic, atmospheric pads, ethereal textures"`
- `"indie folk ballad, coming-of-age themes, acoustic guitar picking"`

## Model Information

| Model | ID | Max Length | Description |
|-------|----|-----------| ------------|
| v1.2 | `ASLP-lab/DiffRhythm-1_2` | 95s | Latest, best quality |
| Base | `ASLP-lab/DiffRhythm-base` | 95s | Stable baseline |
| Full | `ASLP-lab/DiffRhythm-full` | 285s | Long-form generation |

## Error Handling

The API returns standard HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `404`: Task/file not found
- `500`: Server error

## Performance Notes

- Generation time: 2-5 minutes depending on length and hardware
- Memory usage: ~8GB VRAM minimum (chunked mode helps)
- Concurrent generations: Limited by GPU memory
- File cleanup: Automatic after download

## Production Deployment

For production use:

1. Configure CORS origins properly
2. Add authentication/rate limiting
3. Use proper logging and monitoring
4. Set up file storage (S3, etc.)
5. Use a process manager (systemd, supervisor)
6. Add health checks and metrics 