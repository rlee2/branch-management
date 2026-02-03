#!/bin/bash

# Exit on any error
set -e

# Check for branch name argument
if [ "$#" -ne 1 ]; then
    echo "Usage: ./create_branches.sh <branch_name>"
    exit 1
fi

BRANCH_NAME="$1"

# Run ssh-agent and ssh-add
echo "🔐 Starting ssh-agent and adding SSH key..."
eval "$(ssh-agent -s)"

# Update the path below if your key is not in the default location
ssh-add ~/.ssh/github_ed25519

# Now call the Python script with the branch name
echo "🚀 Running Python script to create branch: $BRANCH_NAME"
python3 create_branches.py "$BRANCH_NAME"
