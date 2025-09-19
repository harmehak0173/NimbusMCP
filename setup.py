#!/usr/bin/env python3
"""
Setup script for Weather LLM MCP Project
"""

import os
import subprocess
import sys


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"📦 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"   Error: {e.stderr}")
        return False


def main():
    """Main setup function"""
    print("🚀 Weather LLM MCP Project Setup")
    print("=" * 50)
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        print(f"   Current version: {sys.version}")
        return False
    
    print(f"✅ Python version: {sys.version.split()[0]}")
    
    # Install dependencies
    if not run_command("pip install -r requirements.txt", "Installing Python dependencies"):
        return False
    
    # Create .env file if it doesn't exist
    if not os.path.exists(".env"):
        print("📝 Creating .env file...")
        try:
            with open(".env.example", "r") as src, open(".env", "w") as dst:
                dst.write(src.read())
            print("✅ .env file created from template")
            print("   ⚠️  Please edit .env and add your OpenWeatherMap API key")
        except Exception as e:
            print(f"❌ Failed to create .env file: {e}")
            return False
    else:
        print("✅ .env file already exists")
    
    # Check if API key is configured
    from dotenv import load_dotenv
    load_dotenv()
    
    api_key = os.getenv("OPENWEATHER_API_KEY")
    if not api_key or api_key == "your_api_key_here":
        print("⚠️  OpenWeatherMap API key not configured")
        print("   Please:")
        print("   1. Get a free API key from: https://openweathermap.org/api")
        print("   2. Edit the .env file and replace 'your_api_key_here' with your actual key")
        print("   3. Run 'python test_system.py' to verify the setup")
    else:
        print("✅ OpenWeatherMap API key found")
        
        # Run tests if API key is configured
        print("\n🧪 Running system tests...")
        if run_command("python test_system.py", "System tests"):
            print("\n🎉 Setup completed successfully!")
            print("   You can now run 'python llm_weather_client.py' to start the weather assistant")
        else:
            print("\n⚠️  Setup completed but tests failed")
            print("   Please check your API key and internet connection")
    
    print("\n" + "=" * 50)
    print("Setup complete!")
    
    return True


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
