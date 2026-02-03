# Branch Management Automation

A collection of Python scripts to automate multi-repository workflows on GitHub, including branch creation, pull request generation, and release management.

## Features

- **Multi-Repo Operations**: Perform Git actions across dozens of repositories simultaneously.
- **Unified Configuration**: Manage repository lists in simple `owner/repo` text files with comment support.
- **Interactive PR Review**: Create Pull Requests for all repos and review them sequentially in your browser.
- **Automated Releases**: Generate GitHub releases with automated release notes for multiple repositories.

## Setup

1. **Prerequisites**:
   - Python 3.x
   - Install dependencies: `pip install -r requirements.txt`
   - GitHub Personal Access Token (PAT) with `repo` scope.

2. **Environment**:
   Create a `.env` file in the project root:
   ```env
   GITHUB_TOKEN=your_github_token_here
   ```

3. **Repository Lists**:
   - `repos-full.txt`: The **full list** of all repositories managed by this project. Used by branching and PR scripts to track the entire codebase.
   - `repos-release.txt`: A subset containing only the **active release repositories**. This list defines which repositories are currently undergoing release merging and final release creation.
   Format: `owner/repository` (one per line, `#` for comments).

## Usage

### 1. Create Branches
Creates and pushes a new branch directly on GitHub (from `develop`) across all repos.
```bash
# Uses repos-full.txt via GitHub API
python3 create_branches.py my-feature-branch
```

### 2. Create Pull Requests
Creates PRs to `master` (default) or a specified branch.
```bash
# Uses repos-full.txt
python3 create_prs.py my-feature-branch [base-branch]
```
- **Smart Titles**: Branches starting with `release-` get formatted titles.
- **Interactive Mode**: Prompts to open each PR in the browser (direct to `/changes`).

### 3. Create Releases
Generates GitHub releases for the listed repositories.
```bash
# Uses repos-release.txt
python3 create_releases.py 1.0.0
```

## Project Structure
- `create_branches.py`: Initial branching logic via GitHub API.
- `create_prs.py`: GitHub PR automation with interactive review.
- `create_releases.py`: GitHub Release automation.
- `repos-full.txt`: Target repositories for development.
- `repos-release.txt`: Target repositories for releases.
