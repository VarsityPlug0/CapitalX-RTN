@echo off
cd /d "c:\Users\money\HustleProjects\BevanTheDev\capital x update"
echo Adding all changes...
git add .
echo Committing changes...
git commit -m "Fix template directory order to prioritize CapitalXPlatform templates"
echo Pushing to GitHub...
git push origin main
if errorlevel 1 (
    echo Trying to push to master branch...
    git push origin master
)
echo Done!
pause