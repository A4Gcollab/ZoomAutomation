#!/bin/bash
# This script will forcefully overwrite the remote GitHub repository with your current local project files.
# WARNING: This will delete any history or files on the remote that are not present here.

echo "--- Force pushing all local files to GitHub ---"

# 1. Remove old .git directory to resolve any conflicts or bad state
echo "Removing old .git directory..."
rm -rf .git

# 2. Initialize a new, clean Git repository
echo "Initializing new Git repository..."
git init

# 3. Add the remote repository
echo "Adding remote origin..."
git remote add origin https://github.com/A4Gcollab/ZoomAutomation.git

# 4. Add all files in the current directory to the repository
echo "Adding all files..."
git add .

# 5. Create a new commit
echo "Creating a new commit..."
git commit -m "feat: Complete project-wide sync of frontend and backend"

# 6. Rename the current branch to 'main'
git branch -M main

# 7. Force push to the 'main' branch on GitHub
# The '--force' flag will overwrite the remote repository's history.
echo "Force pushing to GitHub... This will overwrite the remote repository."
git push --force origin main

echo "✅ All files have been pushed to GitHub successfully!"
echo "You can now check your repository: https://github.com/A4Gcollab/ZoomAutomation"
