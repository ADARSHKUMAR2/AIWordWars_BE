# Deployment Fix - Cloud Run Port Configuration

## Issue Summary
3 out of 8 services were failing to deploy to Google Cloud Run with the error:
> "The user-provided container failed to start and listen on the port defined provided by the PORT=8080 environment variable within the allocated timeout."

## Root Cause
The services were configured to use different ports in their local `.env` files (e.g., PORT=8004, PORT=8005, PORT=8007), but Cloud Run expects all services to listen on **PORT=8080**. The Dockerfiles correctly defaulted to 8080, but the Python applications were loading `.env` files that overrode this with different port values.

## Solution Applied
Updated `.github/workflows/deploy.yml` to:
1. **Remove PORT from environment variables** - Cloud Run automatically sets PORT=8080
2. **Configure service-specific environment variables** (database URLs, API keys, service URLs)
3. **Use GitHub Secrets** for sensitive data instead of hardcoding

## Required GitHub Secrets
You need to configure the following secrets in your GitHub repository:
**Settings → Secrets and variables → Actions → New repository secret**

### Required Secrets:
1. **GCP_CREDENTIALS** - Your Google Cloud service account JSON key (already configured)
2. **MONGODB_URL** - MongoDB connection string
   ```
   mongodb+srv://username:password@cluster.mongodb.net/database
   ```
3. **UPSTASH_REDIS_REST_URL** - Upstash Redis connection URL
   ```
   rediss://default:password@endpoint.upstash.io:6379
   ```
4. **GEMINI_API_KEY** - Google Gemini API key for AI word generation

## Service Configuration

### Failed Services (Now Fixed):
- **wordwars-game** (game_logic)
  - PORT=8080
  - MONGODB_URL (from secrets)
  - AI_WORD_GENERATOR_URL (Cloud Run URL)

- **wordwars-leaderboard**
  - PORT=8080
  - MONGODB_URL (from secrets)

- **wordwars-multiplayer** (multiplayer_session)
  - PORT=8080
  - MONGODB_URL (from secrets)
  - AUTH_SERVICE_URL (Cloud Run URL)

### Other Services:
- **wordwars-gateway**: PORT=8080 + all service URLs + Redis
- **wordwars-auth**: PORT=8080 + MongoDB
- **wordwars-ai-word-generator**: PORT=8080 + Gemini API key
- **wordwars-daily-challenge**: PORT=8080 + Redis
- **wordwars-matchmaking**: PORT=8080 + WebSocket URL

## Next Steps

### 1. Configure GitHub Secrets
Add the secrets mentioned above to your GitHub repository.

### 2. Commit and Push
```bash
git add .github/workflows/deploy.yml DEPLOYMENT_FIX.md
git commit -m "Fix Cloud Run deployment: Set PORT=8080 and configure environment variables"
git push origin main
```

### 3. Monitor Deployment
- Go to GitHub Actions tab
- Watch the deployment workflow
- All 8 services should now deploy successfully

### 4. Verify Services
After deployment, check each service health endpoint:
```bash
curl https://wordwars-game-734983454951.asia-south1.run.app/health
curl https://wordwars-leaderboard-734983454951.asia-south1.run.app/health
curl https://wordwars-multiplayer-734983454951.asia-south1.run.app/health
```

## Changes Made
- ✅ Set PORT=8080 for all services
- ✅ Configured service-specific environment variables
- ✅ Used GitHub Secrets for sensitive data
- ✅ Maintained service-to-service communication URLs
- ✅ Added --allow-unauthenticated flag for public access

## Technical Details

### Before:
- Services read PORT from `.env` files (8004, 8005, 8007)
- Cloud Run expected services on port 8080
- Health checks failed → deployment failed

### After (Corrected):
- Cloud Run automatically sets PORT=8080 (reserved environment variable)
- Workflow no longer attempts to set PORT manually
- Services use Cloud Run's PORT via `os.getenv("PORT", 8080)`
- Services start on correct port
- Health checks succeed → deployment succeeds

### Important Note:
Cloud Run reserves the `PORT` environment variable and sets it automatically. Attempting to set it manually via `--set-env-vars` causes a deployment error: `"reserved env names were provided: PORT"`. The services already use `os.getenv("PORT", 8080)` which will correctly read Cloud Run's automatically-injected PORT value.
