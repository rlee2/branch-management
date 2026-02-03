#!/usr/bin/env python3
import requests
import json
import sys
import os

# Load environment variables (simple .env loader)
def load_dotenv(path=".env"):
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    parts = line.strip().split("=", 1)
                    if len(parts) == 2:
                        key, value = parts
                        os.environ[key] = value.strip('"').strip("'")

# Load configuration
load_dotenv()
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN")
REPO_FILE = "repos-full.txt"
SOURCE_BRANCH = "develop"

def create_branch_via_api(repo_owner, repo_name, new_branch, source_branch, token):
    """
    Creates a new branch from a source branch using the GitHub REST API.
    """
    # 1. Get the SHA of the source branch
    ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs/heads/{source_branch}"
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }

    try:
        response = requests.get(ref_url, headers=headers)
        if response.status_code != 200:
            print(f"❌ Error fetching '{source_branch}' for {repo_owner}/{repo_name}: {response.status_code} {response.text}")
            return False
        
        source_sha = response.json()["object"]["sha"]
        
        # 2. Create the new reference
        create_ref_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/git/refs"
        payload = {
            "ref": f"refs/heads/{new_branch}",
            "sha": source_sha
        }
        
        create_res = requests.post(create_ref_url, headers=headers, json=payload)
        if create_res.status_code == 201:
            print(f"✅ Created branch '{new_branch}' in {repo_owner}/{repo_name}")
            return True
        elif create_res.status_code == 422:
            print(f"ℹ️ Branch '{new_branch}' already exists in {repo_owner}/{repo_name}")
            return True
        else:
            print(f"❌ Error creating branch for {repo_owner}/{repo_name}: {create_res.status_code} {create_res.text}")
            return False

    except Exception as e:
        print(f"❌ Exception occurred for {repo_owner}/{repo_name}: {str(e)}")
        return False

def load_repos(file_path):
    """
    Loads repository paths from a text file, skipping empty lines and comments.
    """
    repos = []
    if not os.path.exists(file_path):
        print(f"⚠️ Warning: File {file_path} not found.")
        return repos
        
    with open(file_path, "r") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#"):
                repos.append(line)
    return repos

def main():
    if len(sys.argv) != 2:
        print("Usage: python3 create_branches.py <new_branch_name>")
        sys.exit(1)
        
    new_branch = sys.argv[1]
    
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN not found in environment or .env file.")
        sys.exit(1)
        
    repos = load_repos(REPO_FILE)
    
    if not repos:
        print(f"❌ Error: No repositories found in {REPO_FILE}")
        sys.exit(1)
        
    print(f"� Creating branch '{new_branch}' from '{SOURCE_BRANCH}' for {len(repos)} repositories via API...\n")
    
    success_count = 0
    for repo_path in repos:
        try:
            owner, name = repo_path.split("/")
            if create_branch_via_api(owner, name, new_branch, SOURCE_BRANCH, GITHUB_TOKEN):
                success_count += 1
        except ValueError:
            print(f"❌ Invalid repo format in {REPO_FILE}: {repo_path} (Expected: owner/repo)")

    print(f"\n📊 Processed {len(repos)} repositories. {success_count} success/exists.")

if __name__ == "__main__":
    main()
