# 🚀 DiffRhythm RunPod Serverless Deployment Guide

This guide shows you how to deploy your DiffRhythm container to RunPod Serverless for scalable, on-demand music generation.

## 🎯 **What is RunPod Serverless?**

**RunPod Serverless** is like **AWS Lambda but for GPU workloads**:

- ⚡ **On-demand**: Only runs when you need it (no idle costs)
- 🚀 **Scalable**: Automatically handles multiple requests
- 💰 **Cost-effective**: Pay only for actual generation time
- 🔥 **GPU-powered**: Access to high-end GPUs (RTX 4090, A100, etc.)
- 🌍 **Global**: Multiple regions for low latency

### **How it works:**
1. You upload your container to RunPod
2. RunPod creates an **API endpoint** 
3. Your app calls the endpoint with LRC + prompt
4. RunPod spins up a GPU instance → generates music → returns result
5. Instance shuts down automatically (no ongoing costs)

---

## 🆚 **Serverless vs Your Current Setup**

| Aspect | Your Container | RunPod Serverless |
|--------|---------------|-------------------|
| **Availability** | 24/7 running | On-demand |
| **Cost** | Fixed GPU costs | Pay-per-use |
| **Scaling** | Single instance | Auto-scaling |
| **Maintenance** | Manual updates | Managed service |
| **Global reach** | Single location | Multiple regions |

---

## 📋 **Prerequisites**

1. **Docker image** pushed to Docker Hub (✅ you have this)
2. **RunPod account** (free signup)
3. **RunPod API key**
4. **Credit/payment method** on RunPod

---

## 🛠️ **Step 1: Prepare Your Container for RunPod**

### **1.1 Build RunPod-optimized container:**

```bash
# Build the RunPod version
docker build -f Dockerfile.runpod -t your-username/diffrhythm-runpod:latest .

# Push to Docker Hub
docker push your-username/diffrhythm-runpod:latest
```

### **1.2 Test locally first (recommended):**

```bash
# Test the handler locally
python3 test_runpod_local.py
```

---

## 🚀 **Step 2: Deploy to RunPod Serverless**

### **2.1 Login to RunPod Dashboard**
1. Go to [runpod.io](https://runpod.io)
2. Sign up/Login
3. Navigate to **"Serverless"** → **"Templates"**

### **2.2 Create Template**
1. Click **"New Template"**
2. Fill in details:
   - **Template Name**: `diffrhythm-music-generation`
   - **Container Image**: `your-username/diffrhythm-runpod:latest`
   - **Container Registry Credentials**: Add if private repo
   - **Container Disk**: `20 GB` (for models)
   - **Volume Disk**: `0 GB` (not needed)
   - **Volume Mount Path**: Leave empty
   - **Expose HTTP Ports**: Leave empty
   - **Expose TCP Ports**: Leave empty
   - **Environment Variables**: 
     ```
     CUDA_VISIBLE_DEVICES=0
     PYTHONPATH=/app
     ```

### **2.3 Create Endpoint**
1. Go to **"Serverless"** → **"Endpoints"**
2. Click **"New Endpoint"**
3. Configure:
   - **Endpoint Name**: `diffrhythm-api`
   - **Template**: Select your template
   - **Active Workers**: `0` (auto-scale from 0)
   - **Max Workers**: `3` (adjust based on expected load)
   - **Idle Timeout**: `5 seconds`
   - **Flash Boot**: `Enabled` (faster cold starts)
   - **GPU Types**: Select based on budget
     - **RTX A6000** (recommended for cost/performance)
     - **RTX 4090** (good performance)
     - **A100** (premium option)

4. Click **"Deploy"**

### **2.4 Get Endpoint Details**
After deployment:
1. Copy your **Endpoint ID** (e.g., `abc123def456`)
2. Copy your **API Key** from Settings
3. Your endpoint URL will be: `https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync`

---

## 🧪 **Step 3: Test Your Deployment**

### **3.1 Update test script:**
```python
# In test_runpod_endpoint.py, update:
RUNPOD_ENDPOINT_URL = "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync"
RUNPOD_API_KEY = "YOUR_API_KEY"
```

### **3.2 Run test:**
```bash
python3 test_runpod_endpoint.py
```

### **3.3 Expected output:**
```
✅ Generation successful!
   Generation time: 45.2s
   File size: 16777216 bytes
   Model used: ASLP-lab/DiffRhythm-1_2
🎵 Audio saved: generated_music_runpod.wav
```

---

## 💻 **Step 4: Integrate with Your App**

### **4.1 Frontend Integration (JavaScript):**

```javascript
async function generateMusicRunPod(lrcContent, stylePrompt) {
    const response = await fetch('https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync', {
        method: 'POST',
        headers: {
            'Authorization': 'Bearer YOUR_API_KEY',
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            input: {
                lrc_content: lrcContent,
                ref_prompt: stylePrompt,
                audio_length: 95,
                use_chunked: true
            }
        })
    });
    
    const result = await response.json();
    
    if (result.status === 'COMPLETED' && result.output.success) {
        // Convert base64 to audio blob
        const audioData = atob(result.output.audio_base64);
        const audioBlob = new Blob([audioData], { type: 'audio/wav' });
        const audioUrl = URL.createObjectURL(audioBlob);
        
        return audioUrl;
    } else {
        throw new Error(result.output?.error || 'Generation failed');
    }
}
```

### **4.2 Backend Integration (Python):**

```python
import requests
import base64

def generate_music_runpod(lrc_content, ref_prompt):
    response = requests.post(
        'https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync',
        headers={
            'Authorization': 'Bearer YOUR_API_KEY',
            'Content-Type': 'application/json'
        },
        json={
            'input': {
                'lrc_content': lrc_content,
                'ref_prompt': ref_prompt,
                'audio_length': 95,
                'use_chunked': True
            }
        }
    )
    
    result = response.json()
    
    if result['status'] == 'COMPLETED' and result['output']['success']:
        audio_data = base64.b64decode(result['output']['audio_base64'])
        return audio_data
    else:
        raise Exception(result['output'].get('error', 'Generation failed'))
```

---

## 💰 **Step 5: Cost Optimization**

### **5.1 GPU Selection Guide:**
- **RTX A6000**: ~$0.79/hour (best cost/performance)
- **RTX 4090**: ~$0.69/hour (good for most use cases)  
- **A100**: ~$2.29/hour (premium performance)

### **5.2 Cost Estimation:**
- **Generation time**: ~30-60 seconds per song
- **Cost per song**: ~$0.01-0.04 depending on GPU
- **Monthly cost** (100 songs): ~$1-4

### **5.3 Optimization tips:**
- Use **Flash Boot** for faster cold starts
- Set appropriate **Idle Timeout** (5-10 seconds)
- Monitor usage and adjust **Max Workers**

---

## 🔧 **Step 6: Production Configuration**

### **6.1 Security:**
```bash
# Store API keys securely
export RUNPOD_API_KEY="your-key-here"

# Use environment variables in your app
RUNPOD_ENDPOINT_URL = os.getenv('RUNPOD_ENDPOINT_URL')
```

### **6.2 Error Handling:**
```python
def robust_music_generation(lrc_content, ref_prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return generate_music_runpod(lrc_content, ref_prompt)
        except Exception as e:
            if attempt == max_retries - 1:
                raise e
            time.sleep(2 ** attempt)  # Exponential backoff
```

### **6.3 Monitoring:**
- Check **RunPod Dashboard** for usage stats
- Monitor **response times** and **error rates**
- Set up **alerts** for high usage

---

## 📊 **Benefits for Your App**

### **✅ Advantages:**
- **No server maintenance**: Focus on your app, not infrastructure
- **Global scaling**: Handle users worldwide
- **Cost efficiency**: Pay only for actual usage
- **High availability**: RunPod handles uptime
- **Multiple GPU options**: Choose based on performance needs

### **📈 Use Cases:**
- **Mobile app backend**: Perfect for on-demand music generation
- **Web application**: Handle variable user loads  
- **API service**: Offer music generation as a service
- **Batch processing**: Process multiple songs efficiently

---

## 🛠️ **Troubleshooting**

### **Common Issues:**

#### **Cold Start Timeouts**
```json
{"error": "Function timed out during cold start"}
```
**Solution**: 
- Enable Flash Boot
- Optimize container size
- Pre-load models in handler

#### **Memory Issues**
```json
{"error": "CUDA out of memory"}
```
**Solution**:
- Use `use_chunked: true`
- Select GPU with more VRAM
- Reduce `batch_infer_num`

#### **Model Download Fails**
```json
{"error": "Failed to download model"}
```
**Solution**:
- Increase container disk size
- Check internet connectivity
- Pre-download models in Dockerfile

### **Debug Commands:**
```bash
# Check endpoint logs
curl -H "Authorization: Bearer YOUR_API_KEY" \
     "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/logs"

# Test with minimal input
curl -X POST "https://api.runpod.ai/v2/YOUR_ENDPOINT_ID/runsync" \
     -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"input": {"lrc_content": "[00:00.00]Test", "ref_prompt": "test"}}'
```

---

## 🎉 **Success! You're Ready**

Your DiffRhythm service is now:
- **Globally accessible** via API
- **Auto-scaling** based on demand  
- **Cost-optimized** for real usage
- **Production-ready** for your app

### **Next Steps:**
1. Update your app to use the RunPod endpoint
2. Monitor usage and costs
3. Scale up by adding more workers if needed
4. Consider multiple regions for global users

**Your music generation is now serverless! 🚀🎵** 