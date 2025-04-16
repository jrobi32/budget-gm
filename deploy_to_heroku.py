import os
import subprocess
import random
import string

def generate_secret_key(length=32):
    """Generate a random secret key."""
    return ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(length))

def run_command(command):
    """Run a command and print its output."""
    print(f"Running: {command}")
    process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdout, stderr = process.communicate()
    print(stdout.decode('utf-8'))
    if stderr:
        print(f"Error: {stderr.decode('utf-8')}")
    return process.returncode

def main():
    # Generate a secure secret key
    secret_key = generate_secret_key()
    
    # Check if Heroku CLI is installed
    if run_command("heroku --version") != 0:
        print("Heroku CLI is not installed. Please install it from https://devcenter.heroku.com/articles/heroku-cli")
        return
    
    # Login to Heroku
    if run_command("heroku login") != 0:
        print("Failed to login to Heroku. Please try again.")
        return
    
    # Create a new Heroku app
    app_name = "nba-team-builder-api"
    if run_command(f"heroku create {app_name}") != 0:
        print(f"Failed to create Heroku app {app_name}. It might already exist.")
        print("Continuing with deployment...")
    
    # Set environment variables
    if run_command(f"heroku config:set SECRET_KEY={secret_key} --app {app_name}") != 0:
        print("Failed to set environment variables.")
        return
    
    # Push your code to Heroku
    if run_command(f"git push heroku main --app {app_name}") != 0:
        print("Failed to push code to Heroku.")
        return
    
    print(f"\nDeployment successful! Your backend is now available at https://{app_name}.herokuapp.com")
    print(f"Make sure to update your React app's .env.production file to point to this URL.")

if __name__ == "__main__":
    main() 