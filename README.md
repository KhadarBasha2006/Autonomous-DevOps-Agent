# Autonomous-DevOps-Agent

An AI-powered autonomous DevOps agent that clones GitHub repositories, detects bugs (linting, syntax, logic, type errors, indentation), applies AI-generated fixes, pushes to a new branch, and monitors CI/CD — all autonomously. Features a live React dashboard with score tracking. Built for RIFT 2026. 🤖

## Features

- **Automatic Bug Detection**: Detects multiple bug types:
  - Linting errors (unused imports, debug statements)
  - Syntax errors (missing colons, unmatched brackets)
  - Type errors
  - Indentation issues (tab vs spaces)
  - Import errors

- **AI-Powered Fixes**: Automatically applies fixes to detected bugs
- **CI/CD Pipeline Simulation**: Runs iterations to validate fixes
- **GitHub Integration**: Forks or pushes fixes to a new branch
- **Live Dashboard**: React-based UI with real-time progress tracking
- **Score Tracking**: Calculates scores based on fixes and time

## Tech Stack

- **Frontend**: React, Tailwind CSS, Axios
- **Backend**: FastAPI (Python)
- **Deployment**: Vercel (Serverless)

## Project Structure

```
CICD/
├── api/                    # Vercel serverless API
│   ├── index.py           # FastAPI application
│   ├── agent_logic.py     # Bug detection and fixing logic
│   └── requirements.txt   # Python dependencies
├── frontend/              # React application
│   ├── src/
│   │   ├── App.js        # Main React component
│   │   └── ...
│   └── package.json
├── backend/              # Original backend (local development)
├── vercel.json           # Vercel configuration
└── README.md
```

## Local Development

### Prerequisites

- Node.js and npm
- Python 3.9+
- GitHub Account

### Backend Setup (Local)

```
bash
# Navigate to backend
cd backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install fastapi pydantic uvicorn python-multipart httpx PyGithub

# Run backend
python main.py
```

The backend runs on `http://localhost:8000`

### Frontend Setup

```
bash
# Navigate to frontend
cd frontend

# Install dependencies
npm install

# Run development server
npm start
```

The frontend runs on `http://localhost:3000`

## Vercel Deployment

### Quick Deploy

```
bash
# Install Vercel CLI
npm i -g vercel

# Navigate to project
cd c:/Users/phuss/Documents/cicd-healing-agent/CICD

# Login to Vercel
vercel login

# Deploy
vercel
```

### Environment Variables

After deploying to Vercel, set the following in your Vercel dashboard:

1. Go to **Settings** → **Environment Variables**
2. Add:
   - **Name**: `GITHUB_TOKEN`
   - **Value**: Your GitHub Personal Access Token (with `repo` scope)

To create a GitHub Token:
1. Go to GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
2. Generate new token (classic)
3. Select scopes: `repo`
4. Copy and add to Vercel

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | API info |
| `/health` | GET | Health check |
| `/api/` | GET | API info (Vercel) |
| `/api/health` | GET | Health check (Vercel) |
| `/api/analyze` | POST | Analyze and fix repository |

### Analyze Endpoint

**Request:**
```
json
{
  "repo_url": "https://github.com/username/repo",
  "team_name": "RIFT ORGANISERS",
  "leader_name": "John Doe",
  "github_token": "ghp_xxxxxxxxxxxx"  // Optional
}
```

**Response:**
```
json
{
  "repo_url": "https://github.com/username/repo",
  "team_name": "RIFT ORGANISERS",
  "leader_name": "John Doe",
  "branch_name": "RIFT_ORGANISERS_JOHN_DOE_AI_Fix",
  "branch_url": "https://github.com/username/repo/tree/RIFT_ORGANISERS_JOHN_DOE_AI_Fix",
  "push_status": "Pushed successfully",
  "total_failures_detected": 5,
  "total_fixes_applied": 5,
  "cicd_status": "PASSED",
  "total_time_taken": 45.2,
  "fixes": [...],
  "cicd_runs": [...]
}
```

## Usage

1. Open the deployed application
2. Enter the GitHub repository URL
3. Enter your team name
4. Enter the team leader name
5. (Optional) Enter your GitHub token for forking
6. Click "Run Agent"
7. Watch the analysis and fixing process in real-time
8. View the results and generated branch URL

## Scoring

- Base score: 100 points
- Speed bonus: +10 points if completed under 300 seconds
- Penalty: -2 points per fix over 20

## Limitations

- **Vercel Free Tier**: Maximum execution time is 10 seconds per request
- **Vercel Pro**: Maximum execution time is 60 seconds per request
- Large repositories may timeout on serverless deployment
- For production use with large repos, consider deploying backend separately

## License

MIT

## Author

