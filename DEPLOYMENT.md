# Deployment Guide

This guide covers free deployment options for the Bill Extraction API.

## 🚀 Recommended: Render (Free Tier)

**Render** offers a free tier perfect for FastAPI applications with automatic HTTPS, zero-downtime deployments, and easy setup.

### Prerequisites
- GitHub account (your code is already on GitHub)
- Render account (sign up at https://render.com - free)

### Step 1: Create Render Account
1. Go to https://render.com
2. Sign up with your GitHub account
3. Authorize Render to access your repositories

### Step 2: Create New Web Service
1. Click "New +" → "Web Service"
2. Connect your GitHub account if not already connected
3. Select repository: `PurushotamGupta_Bits_Hyd`
4. Configure the service:
   - **Name**: `bill-extraction-api` (or your preferred name)
   - **Region**: Choose closest to you (e.g., `Oregon (US West)`)
   - **Branch**: `main`
   - **Root Directory**: Leave empty (or `./` if needed)
   - **Runtime**: `Python 3`
   - **Build Command**: 
     ```bash
     pip install --upgrade pip && pip install -e . && pip install -r requirements.txt
     ```
   - **Start Command**: 
     ```bash
     uvicorn bill_extraction_api.app.main:app --host 0.0.0.0 --port $PORT
     ```
   - **Environment**: `Python 3`
   - **Instance Type**: `Free` (512 MB RAM)

### Step 3: Add Environment Variables (Optional)
If you want to use LLM parser, add these in the "Environment" section:
- `BILL_API_PARSER_BACKEND=regex` (default, no API key needed)
- Or for LLM: `BILL_API_PARSER_BACKEND=llm`, `BILL_API_LLM_PROVIDER=openai`, etc.

### Step 4: Deploy
1. Click "Create Web Service"
2. Render will automatically:
   - Clone your repository
   - Install dependencies
   - Build the application
   - Deploy it
3. Wait 5-10 minutes for the first deployment
4. Your API will be live at: `https://your-app-name.onrender.com`

### Step 5: Access Your API
- **API Base URL**: `https://your-app-name.onrender.com`
- **API Docs**: `https://your-app-name.onrender.com/docs`
- **Health Check**: `https://your-app-name.onrender.com/docs` (Swagger UI)

### Important Notes for Render Free Tier
- ⚠️ **Cold Starts**: Free tier services spin down after 15 minutes of inactivity. First request after inactivity may take 30-60 seconds.
- ⚠️ **Resource Limits**: 512 MB RAM, 0.1 CPU
- ✅ **HTTPS**: Automatically enabled
- ✅ **Auto-deploy**: Deploys on every push to `main` branch

---

## 🚂 Alternative: Railway (Free $5 Credit)

**Railway** offers $5 free credit monthly, which is enough for small projects.

### Setup Steps
1. Go to https://railway.app
2. Sign up with GitHub
3. Click "New Project" → "Deploy from GitHub repo"
4. Select your repository
5. Railway auto-detects Python and FastAPI
6. Add start command: `uvicorn bill_extraction_api.app.main:app --host 0.0.0.0 --port $PORT`
7. Deploy!

**Note**: Railway may require a credit card for verification, but won't charge if you stay within free tier.

---

## 🪶 Alternative: Fly.io (Free Tier)

**Fly.io** offers a generous free tier with 3 shared-cpu VMs.

### Setup Steps
1. Install Fly CLI: https://fly.io/docs/getting-started/installing-flyctl/
2. Sign up: `fly auth signup`
3. In your project directory:
   ```bash
   fly launch
   ```
4. Follow prompts (use defaults for most)
5. Deploy: `fly deploy`

---

## 🐳 Docker Deployment (Works with all platforms)

If you prefer Docker, use the included `Dockerfile`:

```bash
# Build image
docker build -t bill-extraction-api .

# Run locally
docker run -p 8000:8000 bill-extraction-api

# Or push to Docker Hub and deploy anywhere
```

---

## 📝 Testing Your Deployed API

Once deployed, test with:

```bash
curl -X POST https://your-app-name.onrender.com/extract-bill-data \
  -H 'Content-Type: application/json' \
  -d '{"document":"https://hackrx.blob.core.windows.net/assets/datathon-IIT/Sample%20Document%201.pdf?sv=2025-07-05&spr=https&st=2025-11-28T10%3A08%3A01Z&se=2025-11-30T10%3A08%3A00Z&sr=b&sp=r&sig=RSfZaGfX%2Fym%2BQT6BqwjAV6hlI1ehE%2FkTDN4sEAJQoPE%3D"}'
```

Or visit: `https://your-app-name.onrender.com/docs` for interactive testing.

---

## 🔧 Troubleshooting Deployment

### Issue: Build fails with "ModuleNotFoundError"
**Solution**: Ensure `pip install -e .` is in the build command.

### Issue: Service crashes on startup
**Solution**: Check logs in Render dashboard. Common issues:
- Port must be `$PORT` (Render sets this automatically)
- Missing system dependencies (poppler-utils) - may need Dockerfile

### Issue: Cold start timeout
**Solution**: This is normal on free tier. Consider:
- Using a health check endpoint to keep service warm
- Upgrading to paid tier
- Using Railway or Fly.io which have better free tiers

### Issue: Memory limit exceeded
**Solution**: 
- Reduce DPI in preprocessing (edit `preprocess.py`)
- Process fewer pages at once
- Upgrade to paid tier

---

## 🎯 Recommended: Render for Quick Deployment

For the fastest, easiest deployment, use **Render**:
- ✅ No credit card required
- ✅ Automatic HTTPS
- ✅ Auto-deploy from GitHub
- ✅ Free tier sufficient for demos/testing
- ⚠️ Cold starts (acceptable for demos)

---

## 📚 Additional Resources

- [Render Documentation](https://render.com/docs)
- [Railway Documentation](https://docs.railway.app)
- [Fly.io Documentation](https://fly.io/docs)

