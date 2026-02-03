import os
import subprocess
import sys

# Function to run a command and return its output with error checking
def run_command(command, cwd=None, env=None):
    print(f"\nRunning: {command} in {cwd or os.getcwd()}")
    try:
        result = subprocess.run(
            command, shell=True, cwd=cwd,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=60
        )
        if result.returncode != 0:
            print(f"❌ Error running command: {command} \n{result.stderr.decode('utf-8')}")
        return result.stdout.decode('utf-8')
    except subprocess.TimeoutExpired:
        print(f"❌ Command timed out: {command}")
        return ""
# Function to load repositories from file, skipping comments and empty lines
def load_repos(file_path):
    repos = []
    if not os.path.exists(file_path):
        return repos
    with open(file_path, 'r') as file:
        for line in file:
            line = line.strip()
            if line and not line.startswith('#'):
                repos.append(line)
    return repos

# Check for correct number of arguments
if len(sys.argv) != 2:
    print("Usage: python3 create_branches.py <new-branch-name>")
    sys.exit(1)

# Branch name to create
new_branch = sys.argv[1]

# Define repos list file and base directory
repos_file = 'repos-full.txt'
base_dir = 'repositories'

# Create base directory if needed
os.makedirs(base_dir, exist_ok=True)

# Load repository paths
repos = load_repos(repos_file)

if not repos:
    print(f"⚠️ No repositories found in {repos_file}")
    sys.exit(0)

# Environment from current shell (with ssh-agent loaded)
env = os.environ.copy()

# Loop through each repository
for repo_path_full in repos:
    # owner/repo format
    repo_name = repo_path_full.split('/')[-1]
    repo_url = f"git@github.com:{repo_path_full}.git"
    repo_path = os.path.join(base_dir, repo_name)

    # Clone if not exists
    if not os.path.exists(repo_path):
        print(f"\n🚀 Cloning repository {repo_name} from {repo_url}...")
        run_command(f"git clone {repo_url} {repo_path}", env=env)
    else:
        print(f"\n📂 Repository {repo_name} already exists, pulling latest changes...")
        status_output = run_command("git status --porcelain", cwd=repo_path, env=env)
        if status_output.strip():
            print(f"⚠️ Uncommitted changes detected in {repo_name}, skipping pull.")
            continue
        run_command("git pull", cwd=repo_path, env=env)

    # Switch to develop and pull
    print(f"🔁 Checking out develop in {repo_name}...")
    run_command("git checkout develop", cwd=repo_path, env=env)
    run_command("git pull origin develop", cwd=repo_path, env=env)

    # Create and push new branch
    print(f"🌱 Creating new branch {new_branch} in {repo_name}...")
    run_command(f"git checkout -b {new_branch}", cwd=repo_path, env=env)
    run_command(f"git push origin {new_branch}", cwd=repo_path, env=env)
    print(f"✅ Branch {new_branch} pushed in {repo_name}.\n")
