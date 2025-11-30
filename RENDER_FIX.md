# Render Deployment Fix

## Issue
Render's Python build environment doesn't install system dependencies (poppler-utils) by default.

## Solution

### Option 1: Update Build Command in Render Dashboard

1. Go to Render Dashboard → Your Service → Settings
2. Find "Build Command"
3. Replace it with:
   ```bash
   apt-get update && apt-get install -y -q poppler-utils libglib2.0-0 libgl1 || echo "Continuing..." && pip install --upgrade pip && pip install -e . && pip install -r requirements.txt
   ```
4. Save and redeploy

### Option 2: Use Docker (More Reliable)

1. In Render Dashboard → Your Service → Settings
2. Enable "Docker" or set "Dockerfile Path" to `Dockerfile`
3. Redeploy

The Dockerfile already has all system dependencies configured.

## Verify It Works

After redeploying, test with a valid document URL. The API should now process PDFs correctly.

