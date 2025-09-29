# PowerShell script to push changes to GitHub
Write-Host "Starting git operations..."

# Navigate to the project directory
Set-Location -Path "c:\Users\money\HustleProjects\BevanTheDev\capital x update"

# Add all changes
Write-Host "1. Adding all changes..."
git add .

# Commit changes
Write-Host "2. Committing changes..."
git commit -m "Fix template directory order to prioritize CapitalXPlatform templates"

# Try to push to main branch
Write-Host "3. Pushing to GitHub (main branch)..."
git push origin main

# If main branch push fails, try master branch
if ($LASTEXITCODE -ne 0) {
    Write-Host "4. Trying to push to master branch..."
    git push origin master
}

Write-Host "Git operations completed!"