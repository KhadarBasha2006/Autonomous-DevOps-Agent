# Vercel Deployment Plan for CICD Healing Agent

## Project Analysis

### Current Structure
- **Frontend**: React app in `frontend/` directory (port 3000)
- **Backend**: FastAPI in `backend/` directory (port 8000)
- **Communication**: Frontend calls `http://localhost:8000/analyze`

### Key Findings from Code Review
1. Frontend `App.js` makes API calls to `http://localhost:8000/analyze`
2. Backend uses FastAPI with endpoints:
   - `GET /` - Root info
   - `GET /health` - Health check
   - `POST /analyze` - Main analysis endpoint
3. Backend has CORS enabled for all origins (`allow_origins=["*"]`)
4. Backend performs git operations (clone, commit, push)
5. Backend requires Python dependencies

---

## Deployment Strategy

### Option: Vercel Serverless Functions
Deploy both frontend and backend as a single Vercel project using:
- Frontend: Static React build served from `/` 
- Backend: Python API routes in `/api` directory

---

## Files to Create/Modify

### 1. Root `vercel.json` - Main configuration
```
json
{
  "builds": [
    {
      "src": "frontend/build/**",
      "use": "@vercel/static"
    },
    {
      "src": "api/**/*.py",
      "use": "@vercel/python",
      "config": { "runtime": "python3.9" }
    }
  ],
  "routes": [
    {
      "src": "/api/(.*)",
      "dest": "/api/$1"
    },
    {
      "src": "/(.*)",
      "dest": "/frontend/build/$1"
    }
  ],
  "env": {
    "GITHUB_TOKEN": "@github_token"
  }
}
```

### 2. `api/` directory - Backend for Vercel
- Copy `backend/main.py` to `api/index.py`
- Copy `backend/agent_logic.py` to `api/agent_logic.py`
- Create `api/requirements.txt` with Python dependencies
- Create `api/__init__.py`

### 3. Update Frontend API URL
- Modify `frontend/src/App.js` to use environment variable `REACT_APP_API_URL`
- Fallback to localhost for development

### 4. Root `package.json` - Build scripts
- Add scripts to build both frontend and prepare backend

---

## Implementation Steps

### Step 1: Create API directory structure
- [ ] Create `api/` directory at root
- [ ] Copy backend files to `api/`
- [ ] Create `api/requirements.txt`
- [ ] Create `api/__init__.py`

### Step 2: Configure Vercel
- [ ] Create `vercel.json` at root
- [ ] Create `.vercelignore` file

### Step 3: Update Frontend
- [ ] Modify `frontend/src/App.js` to use environment variable for API URL
- [ ] Update `frontend/package.json` if needed

### Step 4: Environment Variables
- [ ] Document required environment variables
- [ ] `GITHUB_TOKEN` - For GitHub operations

### Step 5: Build and Deploy
- [ ] Build frontend: `cd frontend && npm run build`
- [ ] Deploy to Vercel: `vercel`

---

## Important Notes

### Backend Modifications Needed
1. FastAPI app must be exposed as `app` for Vercel Python runtime
2. Remove `uvicorn.run()` - Vercel handles the server
3. Update CORS to allow Vercel frontend domain

### Vercel Python Runtime Limitations
- No persistent filesystem (temp files deleted after request)
- Maximum execution time: 10 seconds (free tier), 60 seconds (pro)
- Git operations may timeout - consider using GitHub API instead

### Alternative: Separate Backend Hosting
If backend operations are too heavy for serverless:
- Deploy backend to Render/Heroku/Railway
- Deploy only frontend to Vercel

---

## Required Files to Create

1. `vercel.json` - Vercel configuration
2. `.vercelignore` - Files to ignore
3. `api/index.py` - FastAPI app (modified)
4. `api/agent_logic.py` - Agent logic
5. `api/requirements.txt` - Python dependencies
6. `api/__init__.py` - Package init
