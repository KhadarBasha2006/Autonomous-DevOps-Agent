# Vercel Deployment Instructions

## Prerequisites
1. Node.js and npm installed
2. Vercel CLI installed (`npm i -g vercel`)
3. GitHub account

## Quick Deploy Steps

### Option 1: Deploy via Vercel CLI

```
bash
# 1. Navigate to project directory
cd c:/Users/phuss/Documents/cicd-healing-agent/CICD

# 2. Login to Vercel (if not already logged in)
vercel login

# 3. Deploy to Vercel
vercel
```

Follow the prompts:
- Set up and deploy? **Yes**
- Which scope? **Your Vercel username**
- Link to existing project? **No**
- What's your project's name? **cicd-healing-agent** (or your preferred name)
- In which directory is your code located? **.** (current directory)
- Want to modify settings? **No** (we've configured vercel.json)

### Option 2: Deploy via GitHub

1. Push your code to a GitHub repository
2. Go to [vercel.com](https://vercel.com) and sign in
3. Click "Add New..." → "Project"
4. Import your GitHub repository
5. Configure settings:
   - Framework Preset: **Other**
   - Build Command: (leave empty or use `npm run build` for frontend)
   - Output Directory: (leave empty)
6. Click **Deploy**

## Environment Variables

After deployment, set the following environment variables in Vercel dashboard:

1. Go to your project settings → Environment Variables
2. Add:
   - **GITHUB_TOKEN**: Your GitHub Personal Access Token (with repo permissions)

To create a GitHub Token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Select scopes: `repo`, `read:user`
4. Copy the token and add it to Vercel

## Testing the Deployment

After deployment:
1. Your frontend will be at: `https://your-project.vercel.app`
2. Your API will be at: `https://your-project.vercel.app/api`

Test the API:
```
bash
curl https://your-project.vercel.app/api/health
```

## Local Development

To run locally with the full stack:

```
bash
# Terminal 1 - Backend
cd api
pip install -r requirements.txt
python index.py

# Terminal 2 - Frontend  
cd frontend
npm install
npm start
```

The frontend will run on `http://localhost:3000` and the backend on `http://localhost:8000`.

## Important Notes

1. **Execution Time Limits**: Vercel has limits (10s free, 60s pro). The backend operations may timeout for large repositories.

2. **Serverless Nature**: Each request starts a new container. No persistent filesystem - temp files are deleted after each request.

3. **Git Operations**: Git clone/push operations may timeout. Consider using GitHub API instead for production.

4. **CORS**: The API is configured to allow requests from your Vercel domain. Update `allowed_origins` in `api/index.py` if needed.

## Troubleshooting

### 502 Error
- Check if the API is starting correctly
- Check Vercel function logs

### 504 Timeout
- The operation took too long
- Reduce `max_iterations` in `api/index.py`
- Consider using a separate backend service (Render, Heroku) for heavy operations

### CORS Errors
- Update `allowed_origins` in `api/index.py` to include your Vercel domain

## Files Created for Deployment

- `api/` - FastAPI backend for Vercel serverless
- `vercel.json` - Vercel configuration
- `.vercelignore` - Files to ignore during deployment
- `frontend/.env.local` - Local development config
- `frontend/.env.production` - Production config template
