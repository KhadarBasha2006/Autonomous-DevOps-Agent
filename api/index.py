import os
import re
import subprocess
import time
import json
import shutil
import zipfile
import urllib.request
import ssl
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict

# Import the agent logic
from agent_logic import CodeAgent

app = FastAPI(title="DevOps Agent API")

# Configure CORS for production - update this to your Vercel domain
vercel_domain = os.getenv("VERCEL_URL", "")
allowed_origins = [
    "http://localhost:3000",
    "http://localhost:8000",
    "https://" + vercel_domain if vercel_domain else None
]
allowed_origins = [o for o in allowed_origins if o]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if allowed_origins else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class AnalyzeRequest(BaseModel):
    repo_url: str
    team_name: str
    leader_name: str
    github_token: Optional[str] = ""

# Get token from request or environment variable
def get_github_token(request_token: str = "") -> str:
    """Get GitHub token from request or environment variable
    
    Returns empty string if no token provided - will push directly to original repo
    """
    if request_token:
        print("Using GitHub token from request")
        return request_token
    # Try to get from environment
    env_token = os.getenv("GITHUB_TOKEN", "")
    if env_token:
        print("Using GitHub token from environment variable GITHUB_TOKEN")
        return env_token
    # No token provided - will commit directly to original repository if permissions allow
    print("No GitHub token provided - will attempt to commit directly to original repository")
    return ""

def run_command(cmd, cwd=None, ignore_error=False):
    """Cross-platform command execution
    
    Args:
        cmd: Command to execute
        cwd: Working directory
        ignore_error: If True, don't raise exception on non-zero exit code
    """
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            cwd=cwd,
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0 and not ignore_error:
            print(f"Command failed: {cmd}")
            print(f"Error: {result.stderr}")
        return result
    except FileNotFoundError as e:
        if not ignore_error:
            raise HTTPException(status_code=500, detail=f"Command not found: {str(e)}")
        return subprocess.CompletedProcess(cmd, 1, '', str(e))
    except Exception as e:
        if not ignore_error:
            raise HTTPException(status_code=500, detail=f"Command failed: {str(e)}")
        return subprocess.CompletedProcess(cmd, 1, '', str(e))

def sanitize_filename(filename):
    """Remove invalid characters from filename"""
    return re.sub(r'[<>:"/\\|?*]', '_', filename)

def clone_with_token(repo_url: str, clone_dir: str, token: str) -> tuple:
    """Clone repository using GitHub token for authentication"""
    
    # Extract owner and repo
    parts = repo_url.rstrip('/').replace('.git', '').split('/')
    owner = parts[-2] if len(parts) >= 2 else ""
    repo_name = parts[-1] if len(parts) >= 1 else ""
    
    if not owner or not repo_name:
        return False, "Invalid repository URL"
    
    # Try different branch names
    branches = ['main', 'master', 'develop']
    
    for branch in branches:
        # Clone with token authentication
        if token:
            # Use HTTPS with token
            auth_url = f"https://{token}@github.com/{owner}/{repo_name}.git"
            cmd = f'git clone --branch {branch} --depth 1 "{auth_url}" "{clone_dir}"'
        else:
            # Try without auth (public repo)
            cmd = f'git clone --branch {branch} --depth 1 "{repo_url}" "{clone_dir}"'
        
        result = run_command(cmd)
        
        if result.returncode == 0 and os.path.exists(clone_dir):
            try:
                files = os.listdir(clone_dir)
                if len(files) > 0:
                    return True, f"Cloned via git (branch: {branch})"
            except:
                pass
    
    return False, "Git clone failed"

def download_and_extract_zip(repo_url, extract_to, token=""):
    """Download repo as ZIP and extract it"""
    
    zip_url = repo_url.rstrip('/')
    if zip_url.endswith('.git'):
        zip_url = zip_url[:-4]
    
    # Try different branches
    branch_zip_urls = [
        f"{zip_url}/archive/refs/heads/main.zip",
        f"{zip_url}/archive/refs/heads/master.zip",
    ]
    
    os.makedirs(extract_to, exist_ok=True)
    
    for zip_url in branch_zip_urls:
        print(f"Trying to download: {zip_url}")
        try:
            temp_zip = os.path.join(extract_to, f"repo_{int(time.time())}.zip")
            
            # Create SSL context
            try:
                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                urllib.request.urlretrieve(zip_url, temp_zip)
            except:
                # Fallback without SSL context
                urllib.request.urlretrieve(zip_url, temp_zip)
            
            if os.path.exists(temp_zip) and zipfile.is_zipfile(temp_zip):
                with zipfile.ZipFile(temp_zip, 'r') as zip_ref:
                    zip_ref.extractall(extract_to)
                    
                    dirs = [d for d in os.listdir(extract_to) if os.path.isdir(os.path.join(extract_to, d)) and not d.startswith('.')]
                    
                    if dirs:
                        extracted_repo_dir = os.path.join(extract_to, dirs[0])
                        for item in os.listdir(extracted_repo_dir):
                            src = os.path.join(extracted_repo_dir, item)
                            dst = os.path.join(extract_to, item)
                            if os.path.exists(dst):
                                shutil.rmtree(dst, ignore_errors=True)
                            shutil.move(src, dst)
                        
                        shutil.rmtree(extracted_repo_dir, ignore_errors=True)
                
                try:
                    if os.path.exists(temp_zip):
                        os.remove(temp_zip)
                except:
                    pass
                
                return True, "Downloaded via ZIP"
            
            if os.path.exists(temp_zip):
                try:
                    os.remove(temp_zip)
                except:
                    pass
            
        except Exception as e:
            print(f"Failed to download from {zip_url}: {e}")
            continue
    
    return False, "Could not download repo as ZIP"

def get_repo_info_from_url(repo_url):
    """Extract owner and repo name from GitHub URL"""
    parts = repo_url.rstrip('/').replace('.git', '').split('/')
    if len(parts) >= 2:
        return parts[-2], parts[-1]
    return None, None

def get_authenticated_user(token):
    """Get the authenticated GitHub user from token"""
    try:
        import urllib.request
        import json
        req = urllib.request.Request(
            'https://api.github.com/user',
            headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
        )
        with urllib.request.urlopen(req, timeout=5) as response:
            data = json.loads(response.read().decode())
            username = data.get('login')
            if username:
                print(f"Successfully authenticated as: {username}")
                return username
    except Exception as e:
        print(f"REST API method failed: {e}")
        pass
    
    # Try PyGithub if available
    try:
        from github import Github
        g = Github(token)
        user = g.get_user()
        username = user.login
        if username:
            print(f"Successfully authenticated as: {username}")
            return username
    except Exception as e:
        print(f"PyGithub method failed: {e}")
        pass
    
    return None

def fork_repository(original_owner, repo_name, token):
    """Fork a repository to the authenticated user's account
    
    Returns:
        tuple: (success: bool, message: str, fork_owner: str or None)
    """
    try:
        import urllib.request
        import json
        
        # Get authenticated user first
        target_user = get_authenticated_user(token)
        if not target_user:
            return False, "Could not authenticate user", None
        
        print(f"Target user: {target_user}")
        
        # Check if fork already exists
        check_url = f"https://api.github.com/repos/{target_user}/{repo_name}"
        try:
            req = urllib.request.Request(
                check_url,
                headers={'Authorization': f'token {token}', 'Accept': 'application/vnd.github.v3+json'}
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                print(f"Fork already exists at {target_user}/{repo_name}")
                return True, "Fork already exists", target_user
        except urllib.error.HTTPError as e:
            if e.code != 404:
                return False, f"Error checking fork: {e}", None
        except Exception as e:
            print(f"Check fork error: {e}")
        
        # Create the fork
        fork_url = f"https://api.github.com/repos/{original_owner}/{repo_name}/forks"
        data = json.dumps({"owner": target_user}).encode('utf-8')
        
        req = urllib.request.Request(
            fork_url,
            data=data,
            headers={
                'Authorization': f'token {token}',
                'Accept': 'application/vnd.github.v3+json',
                'Content-Type': 'application/json'
            },
            method='POST'
        )
        
        print(f"Creating fork from {original_owner}/{repo_name} to {target_user}/{repo_name}...")
        with urllib.request.urlopen(req, timeout=30) as response:
            fork_data = json.loads(response.read().decode())
            print(f"Fork created successfully!")
            time.sleep(2)
            return True, f"Forked to {target_user}/{repo_name}", target_owner
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if hasattr(e, 'read') else str(e)
        print(f"HTTP Error {e.code}: {error_body}")
        if e.code == 422:
            target_user = get_authenticated_user(token)
            return True, "Repository already forked", target_user
        return False, f"Failed to fork: {error_body}", None
    except Exception as e:
        print(f"Fork error: {e}")
        return False, f"Failed to fork: {str(e)}", None

def commit_and_push(repo_dir, branch_name, token, repo_url, is_user_token=False):
    """Commit fixes and push to GitHub
    
    Note: This may timeout on Vercel serverless - consider using GitHub API instead
    """
    original_owner, repo_name = get_repo_info_from_url(repo_url)
    
    if not original_owner or not repo_name:
        return None, "Could not parse repository info from URL"
    
    # Determine target owner based on token type
    if is_user_token:
        target_owner = get_authenticated_user(token)
        if not target_owner:
            return None, "Could not authenticate with provided token. Please verify it's valid."
        
        print(f"\nAttempting to fork repository {original_owner}/{repo_name} to user account {target_owner}...")
        fork_success, fork_msg, fork_owner = fork_repository(original_owner, repo_name, token)
        
        if not fork_success:
            return None, f"Failed to fork repository: {fork_msg}"
        
        if fork_owner:
            target_owner = fork_owner
        
        print(f"Using user's GitHub account (forked): {target_owner}")
    else:
        target_owner = original_owner
        print(f"No token provided - pushing directly to original repository: {target_owner}")
    
    # Configure git
    run_command('git config user.email "ai-agent@rift.dev"', cwd=repo_dir)
    run_command('git config user.name "AI Agent"', cwd=repo_dir)
    run_command('git config init.defaultBranch main', cwd=repo_dir)
    
    if is_user_token:
        print("Waiting for GitHub to process the fork...")
        time.sleep(3)
    
    # Reset git remote and reinitialize if needed
    if os.path.exists(os.path.join(repo_dir, '.git')):
        run_command('git remote remove origin', cwd=repo_dir, ignore_error=True)
    else:
        run_command('git init', cwd=repo_dir)
    
    # Add the target remote
    if token:
        push_url = f"https://{token}@github.com/{target_owner}/{repo_name}.git"
    else:
        push_url = f"https://github.com/{target_owner}/{repo_name}.git"
    
    run_command(f'git remote add origin "{push_url}"', cwd=repo_dir)
    
    # Checkout new branch
    run_command(f'git checkout -b {branch_name}', cwd=repo_dir, ignore_error=True)
    run_command(f'git checkout {branch_name}', cwd=repo_dir, ignore_error=True)
    
    # Add all changes
    run_command('git add -A', cwd=repo_dir)
    
    # Check if there are changes to commit
    result = run_command('git status --porcelain', cwd=repo_dir)
    if not result.stdout.strip():
        return None, "No changes to commit"
    
    # Commit
    run_command('git commit -m "[AI-AGENT] Auto-fixes applied by DevOps Agent"', cwd=repo_dir)
    
    # Try to push
    print(f"Attempting to push to: {push_url}")
    push_result = run_command(f'git push -u origin {branch_name}', cwd=repo_dir)
    
    if push_result.returncode == 0:
        if is_user_token:
            branch_link = f"https://github.com/{target_owner}/{repo_name}/tree/{branch_name}"
        else:
            branch_link = repo_url.rstrip('.git')
        return branch_link, "Successfully pushed"
    else:
        error_msg = push_result.stderr if push_result.stderr else push_result.stdout
        print(f"Push failed with error: {error_msg}")
        
        if not token:
            return None, f"Push to {target_owner}/{repo_name} failed. You may need to provide GitHub credentials or a valid GitHub token. Error: {error_msg}"
        
        if "404" in error_msg or "not found" in error_msg:
            return None, f"Repository not found in {target_owner}'s account. Please fork the repository first: https://github.com/{original_owner}/{repo_name}/fork"
        elif "Permission denied" in error_msg or "403" in error_msg:
            return None, f"Permission denied. Make sure your token has push access to {target_owner}/{repo_name}"
        else:
            return None, f"Push failed: {error_msg}"

@app.get("/")
def read_root():
    return {
        "message": "DevOps Agent API is running",
        "status": "active",
        "version": "1.0.0",
        "description": "AI-powered CI/CD healing agent for automated code analysis and fixes",
        "endpoints": {
            "GET /": "API info and available endpoints",
            "GET /health": "Health check and system status",
            "POST /analyze": "Analyze repository and apply AI fixes"
        },
        "features": [
            "Automatic bug detection",
            "AI-powered code fixes",
            "GitHub integration with token authentication",
            "CI/CD pipeline validation",
            "Automated branch creation and push"
        ],
        "deployment": "Vercel Serverless"
    }

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "api_active": True,
        "backend_server": "running",
        "deployment": "vercel",
        "cors_enabled": True,
        "timestamp": time.time()
    }

@app.post("/analyze")
async def analyze_repo(req: AnalyzeRequest):
    """
    Analyze a GitHub repository and apply AI fixes.
    
    Note: This endpoint has limited execution time on Vercel (10-60 seconds).
    For long-running operations, consider using GitHub Actions or a separate backend.
    """
    start_time = time.time()
    
    # Validate inputs
    if not req.repo_url or not req.team_name or not req.leader_name:
        raise HTTPException(status_code=400, detail="All fields are required")
    
    if not req.repo_url.startswith("http://") and not req.repo_url.startswith("https://"):
        raise HTTPException(status_code=400, detail="Invalid repository URL")
    
    # Use fixed maximum iterations (reduced for serverless)
    max_iterations = 3
    
    # Get GitHub token
    github_token = get_github_token(req.github_token)
    is_user_token = bool(req.github_token)
    
    if is_user_token:
        token_source = "User provided token"
    elif github_token:
        token_source = "Environment variable (GITHUB_TOKEN)"
    else:
        token_source = "No token - pushing directly to original repository"
    print(f"Using: {token_source}")
    
    # Branch name format
    branch_name = f"{req.team_name.upper().replace(' ', '_')}_{req.leader_name.upper().replace(' ', '_')}_AI_Fix"
    
    # Repository setup
    repo_name = req.repo_url.split("/")[-1].replace(".git", "")
    repo_name = sanitize_filename(repo_name)
    
    # Use /tmp for Vercel (ephemeral filesystem)
    temp_dir = "/tmp/temp_repos"
    os.makedirs(temp_dir, exist_ok=True)
    
    timestamp = int(time.time())
    clone_dir = os.path.join(temp_dir, f"{repo_name}_{timestamp}")
    
    print(f"Downloading {req.repo_url} to {clone_dir}...")
    
    # Configure git
    run_command("git config --global core.longpaths true")
    
    # Try cloning with token
    success = False
    message = ""
    
    success, message = clone_with_token(req.repo_url, clone_dir, github_token)
    
    # Fallback to ZIP download
    if not success:
        print("Git clone failed, trying ZIP download...")
        success, message = download_and_extract_zip(req.repo_url, clone_dir, github_token)
    
    if not success:
        raise HTTPException(status_code=400, detail=f"Failed to download repository: {message}")
    
    if not os.path.exists(clone_dir):
        raise HTTPException(status_code=400, detail="Download failed - directory not created")
    
    try:
        files = [f for f in os.listdir(clone_dir) if not f.startswith('.')]
        if not files:
            raise HTTPException(status_code=400, detail="Repository is empty")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Error accessing repository: {str(e)}")
    
    # Run the Agent
    try:
        print(f"Executing agent with max_iterations: {max_iterations}")
        agent = CodeAgent(clone_dir, github_token=github_token)
        agent_result = agent.execute(max_iterations=max_iterations)
        print(f"Agent execution completed with {agent_result.get('total_iterations', 0)} iterations")
    except Exception as e:
        print(f"Agent error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent execution failed: {str(e)}")
    
    # Commit and Push to GitHub
    branch_url = None
    push_status = "Not pushed"
    
    print(f"Attempting to push branch to GitHub repository...")
    push_url, push_msg = commit_and_push(clone_dir, branch_name, github_token, req.repo_url, is_user_token=is_user_token)
    if push_url:
        branch_url = push_url
        push_status = "Pushed successfully"
        if is_user_token:
            print(f"Branch pushed to user's GitHub: {push_url}")
        else:
            print(f"Branch pushed to repository: {push_url}")
    else:
        push_status = f"Push skipped: {push_msg}"
        print(f"Push skipped: {push_msg}")
    
    # Generate branch URL if not pushed
    if not branch_url:
        repo_owner, repo_name = get_repo_info_from_url(req.repo_url)
        if repo_owner and repo_name:
            if is_user_token:
                target_owner = get_authenticated_user(github_token)
                if target_owner:
                    branch_url = f"https://github.com/{target_owner}/{repo_name}/tree/{branch_name}"
                else:
                    branch_url = f"https://github.com/{repo_owner}/{repo_name}/tree/{branch_name}"
            else:
                branch_url = req.repo_url.rstrip('.git')
        else:
            branch_url = f"{req.repo_url.rstrip('.git')}/tree/{branch_name}"
    
    # Prepare Response
    duration = round(time.time() - start_time, 2)
    
    cicd_status = "PASSED"
    if agent_result.get('cicd_runs'):
        cicd_status = agent_result['cicd_runs'][-1].get('status', 'PASSED')
    
    result_data = {
        "repo_url": req.repo_url,
        "team_name": req.team_name,
        "leader_name": req.leader_name,
        "branch_name": branch_name,
        "branch_url": branch_url,
        "push_status": push_status,
        "token_used": token_source,
        "push_destination": "User's GitHub Account (Forked)" if is_user_token else "Original Repository",
        "max_iterations_used": max_iterations,
        "total_failures_detected": agent_result.get('unique_bugs', 0),
        "total_fixes_applied": len(agent_result.get('fixes', [])),
        "cicd_status": cicd_status,
        "total_time_taken": duration,
        "total_iterations": agent_result.get('total_iterations', 1),
        "fixes": agent_result.get('fixes', []),
        "cicd_runs": agent_result.get('cicd_runs', [])
    }
    
    # Cleanup temp directory
    try:
        if os.path.exists(clone_dir):
            shutil.rmtree(clone_dir, ignore_errors=True)
    except Exception as e:
        print(f"Cleanup warning: {e}")
    
    return result_data

# For Vercel: export the app
# The app is already defined as 'app' above
