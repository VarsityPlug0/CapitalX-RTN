import subprocess
import sys

def run_git_command(command):
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"Success: {result.stdout}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: {e.stderr}")
        return False

# Add all changes
print("Adding changes...")
if run_git_command("git add ."):
    # Commit changes
    print("Committing changes...")
    if run_git_command('git commit -m "Fix template directory order to prioritize CapitalXPlatform templates"'):
        # Push to main branch
        print("Pushing to GitHub...")
        if run_git_command("git push origin main"):
            print("Successfully pushed changes to GitHub!")
        else:
            # Try master branch if main fails
            print("Trying master branch...")
            run_git_command("git push origin master")
    else:
        print("Failed to commit changes")
else:
    print("Failed to add changes")