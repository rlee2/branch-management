import os
import sys
import json
import argparse
import requests

# Load environment variables (simple .env loader)
def load_dotenv(path=".env"):
    if os.path.exists(path):
        with open(path, "r") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value.strip('"').strip("'")

load_dotenv()

# Provide your GitHub personal access token via environment variable or .env
github_token = os.getenv("GITHUB_TOKEN")
repofile = "repos-release.txt"

# Replace this with your desired target branch
target_branch = "master"

def create_github_release(repo_owner, repo_name, tag_name, target_branch, github_token=None):
    """
    Creates a GitHub release with the specified parameters using GitHub's "Generate release notes" feature.

    :param repo_owner: Owner of the repository (e.g., "octocat").
    :param repo_name: Name of the repository (e.g., "Hello-World").
    :param tag_name: The tag name for the release.
    :param target_branch: The branch the release is created from.
    :param github_token: GitHub personal access token.
    :return: Response JSON from GitHub API.
    """

    if not github_token:
        raise ValueError("GitHub token is required to authenticate the request.")

    url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases"

    headers = {
        "Authorization": f"Bearer {github_token}",
        "Accept": "application/vnd.github+json"
    }

    payload = {
        "tag_name": tag_name,
        "target_commitish": target_branch,
        "name": f"Release {tag_name}",
        "generate_release_notes": True
    }

    response = requests.post(url, headers=headers, data=json.dumps(payload))

    if response.status_code == 201:
        print(f"Release created successfully for {repo_name} with tag {tag_name}!")
    else:
        print(f"Failed to create release for {repo_name}: {response.status_code} {response.text}")

    return response.json()

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

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Create GitHub releases for repositories listed in repos-release.txt")
    parser.add_argument("tag_name", help="Tag name for the release (e.g., v1.0.0)")
    args = parser.parse_args()


    # Read repos from repos-release.txt
    repos = load_repos(repofile)

    if not repos:
        print(f"⚠️ No repositories found in {repofile}")
        sys.exit(0)

    for repo in repos:
        try:
            repo_owner, repo_name = repo.split("/")
            create_github_release(
                repo_owner,
                repo_name,
                args.tag_name,
                target_branch,
                github_token
            )
        except ValueError:
            print(f"Invalid repo format: {repo}. Expected format is 'owner/repository'.")
