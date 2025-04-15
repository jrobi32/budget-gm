#!/usr/bin/env python
"""
Deployment script for NBA Team Builder
This script helps prepare the application for deployment
"""

import os
import shutil
import subprocess
import sys

def check_dependencies():
    """Check if all required dependencies are installed"""
    try:
        import flask
        import pandas
        import numpy
        print("✅ All dependencies are installed")
        return True
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("Please run: pip install -r requirements.txt")
        return False

def create_data_directory():
    """Create the data directory if it doesn't exist"""
    os.makedirs('data/challenges', exist_ok=True)
    print("✅ Data directory created")

def check_player_pool():
    """Check if player_pool.json exists"""
    if os.path.exists('player_pool.json'):
        print("✅ player_pool.json found")
        return True
    else:
        print("❌ player_pool.json not found")
        print("Please run player_pool_data.py first")
        return False

def main():
    """Main deployment function"""
    print("🚀 NBA Team Builder Deployment Helper")
    print("=====================================")
    
    # Check dependencies
    if not check_dependencies():
        return
    
    # Create data directory
    create_data_directory()
    
    # Check player pool
    if not check_player_pool():
        return
    
    print("\n✅ Your application is ready for deployment!")
    print("\nTo deploy to Python Anywhere:")
    print("1. Create an account at https://www.pythonanywhere.com/")
    print("2. Upload your project files")
    print("3. Create a new web app using Flask")
    print("4. Set the source code directory to your project directory")
    print("5. Set the WSGI configuration file to wsgi.py")
    print("6. Install the required packages: pip install -r requirements.txt")
    print("7. Reload your web app")
    
    print("\nTo run locally:")
    print("python app.py")

if __name__ == "__main__":
    main() 