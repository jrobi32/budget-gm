import os
import shutil
import subprocess

# Source directory (your React app)
source_dir = 'nba-team-builder-react'

# Destination directory (new repository for Netlify)
dest_dir = 'budget-gm-frontend'

# Create destination directory if it doesn't exist
if not os.path.exists(dest_dir):
    os.makedirs(dest_dir)

# Copy all files from source to destination
for item in os.listdir(source_dir):
    source_item = os.path.join(source_dir, item)
    dest_item = os.path.join(dest_dir, item)
    
    if os.path.isdir(source_item):
        if item != '.git':  # Skip .git directory
            shutil.copytree(source_item, dest_item, dirs_exist_ok=True)
    else:
        shutil.copy2(source_item, dest_item)

# Update the .env.production file to point to your Heroku backend
env_prod_path = os.path.join(dest_dir, '.env.production')
with open(env_prod_path, 'w') as f:
    f.write('REACT_APP_API_URL=https://nba-team-builder-api.herokuapp.com')

print(f"React app files copied to {dest_dir}")
print("Next steps:")
print("1. cd budget-gm-frontend")
print("2. git init")
print("3. git add .")
print("4. git commit -m 'Initial commit'")
print("5. git remote add origin https://github.com/jrobi32/budget-gm-frontend.git")
print("6. git push -u origin main")
print("7. Deploy to Netlify from the budget-gm-frontend repository") 