#!/usr/bin/env python3
import os
import sys
import json
import webbrowser
import requests

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
REPO_FILE = "repos.txt"
DEFAULT_BASE_BRANCH = "master"

def create_pull_request(repo_owner, repo_name, head_branch, base_branch, token):
    """
    Creates a GitHub pull request using the REST API.
    Returns the PR URL if successful or already exists, else None.
    """
    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    
    # Determine the PR title
    if head_branch.startswith("release-"):
        # Format: release-3.17.0-20260130 -> Release 3.17.0-20260130
        title = head_branch.replace("release-", "Release ", 1)
    else:
        title = f"Merge {head_branch} into {base_branch}"

    payload = {
        "title": title,
        "head": head_branch,
        "base": base_branch,
        "body": f"Automated pull request to merge changes from {head_branch} into {base_branch}."
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        
        if response.status_code == 201:
            pr_data = response.json()
            print(f"✅ Created PR for {repo_owner}/{repo_name}")
            return pr_data['html_url']
        elif response.status_code == 422:
            # Often means PR already exists, try to find the existing one
            error_data = response.json()
            message = error_data.get("errors", [{}])[0].get("message", "Validation failed")
            if "A pull request already exists" in message:
                print(f"ℹ️ PR already exists for {repo_owner}/{repo_name}")
                # Fetch existing PR to get URL
                prs_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/pulls"
                params = {"head": f"{repo_owner}:{head_branch}", "base": base_branch, "state": "open"}
                pr_res = requests.get(prs_url, headers=headers, params=params)
                if pr_res.status_code == 200 and pr_res.json():
                    return pr_res.json()[0]['html_url']
            else:
                print(f"❌ Failed to create PR for {repo_owner}/{repo_name}: {message}")
        else:
            print(f"❌ Error {response.status_code} for {repo_owner}/{repo_name}: {response.text}")
            
    except Exception as e:
        print(f"❌ Exception occurred for {repo_owner}/{repo_name}: {str(e)}")
    
    return None

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
    if len(sys.argv) < 2:
        print("Usage: python3 create_prs.py <head-branch-name> [base-branch-name]")
        sys.exit(1)
        
    head_branch = sys.argv[1]
    base_branch = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_BASE_BRANCH
    
    if not GITHUB_TOKEN:
        print("❌ Error: GITHUB_TOKEN not found in environment or .env file.")
        sys.exit(1)
        
    repos = load_repos(REPO_FILE)
    
    if not repos:
        print(f"❌ Error: No repositories found in {REPO_FILE}")
        sys.exit(1)
        
    print(f"🚀 Creating PRs from '{head_branch}' to '{base_branch}' for {len(repos)} repositories...\n")
    
    pr_urls = []
    for repo_path in repos:
        try:
            owner, name = repo_path.split("/")
            url = create_pull_request(owner, name, head_branch, base_branch, GITHUB_TOKEN)
            if url:
                pr_urls.append(url)
        except ValueError:
            print(f"❌ Invalid repo format in {REPO_FILE}: {repo_path} (Expected: owner/repo)")

    if pr_urls:
        print("\n🔗 Created/Existing Pull Requests (Changes View):")
        for url in pr_urls:
            print(f"{url}/changes")
        
        print("\n👀 Would you like to review them in your browser now? (Y/n): ", end="", flush=True)
        review_all = sys.stdin.readline().strip().lower()
        if review_all != 'n':
            for i, url in enumerate(pr_urls):
                full_url = f"{url}/changes"
                print(f"\n[{i+1}/{len(pr_urls)}] Opening: {full_url}")
                webbrowser.open(full_url)
                
                if i < len(pr_urls) - 1:
                    print("👉 Press Enter to open the next PR (or 'q' to quit): ", end="", flush=True)
                    choice = sys.stdin.readline().strip().lower()
                    if choice == 'q':
                        break
            print("\n✅ Review session complete.")
    else:
        print("\n⚠️ No pull requests were created or found.")

if __name__ == "__main__":
    main()
