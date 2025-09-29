import os
import sys
import subprocess

def run_command(cmd):
    """Run a command and return the result"""
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, cwd=r"c:\Users\money\HustleProjects\BevanTheDev\capital x update")
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def main():
    print("Starting git operations...")
    
    # Add all changes
    print("1. Adding all changes...")
    success, stdout, stderr = run_command("git add .")
    if not success:
        print(f"Failed to add changes: {stderr}")
        return False
    print("Successfully added changes")
    
    # Commit changes
    print("2. Committing changes...")
    success, stdout, stderr = run_command('git commit -m "Fix template directory order to prioritize CapitalXPlatform templates"')
    if not success:
        if "nothing to commit" in stderr or "no changes added to commit" in stderr:
            print("No changes to commit, continuing...")
        else:
            print(f"Failed to commit changes: {stderr}")
            return False
    else:
        print("Successfully committed changes")
    
    # Try to push to main branch
    print("3. Pushing to GitHub (main branch)...")
    success, stdout, stderr = run_command("git push origin main")
    if not success:
        print(f"Failed to push to main: {stderr}")
        print("4. Trying to push to master branch...")
        success, stdout, stderr = run_command("git push origin master")
        if not success:
            print(f"Failed to push to master: {stderr}")
            return False
        else:
            print("Successfully pushed to master branch")
    else:
        print("Successfully pushed to main branch")
    
    print("All operations completed successfully!")
    return True

if __name__ == "__main__":
    try:
        success = main()
        if success:
            print("Git push completed successfully!")
        else:
            print("Git push failed!")
            sys.exit(1)
    except Exception as e:
        print(f"Error occurred: {e}")
        sys.exit(1)