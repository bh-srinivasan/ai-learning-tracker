import os
import sys

# Change to the app directory
os.chdir(r"c:\Users\bhsrinivasan\Downloads\Learning\Vibe Coding\AI_Learning")

# Add the directory to Python path
sys.path.insert(0, os.getcwd())

print("🚀 Starting AI Learning Tracker")
print("=" * 40)
print("🌐 URL: http://localhost:5000")
print("=" * 40)

# Import and run the app
try:
    import app
    if __name__ == "__main__":
        app.app.run(host='0.0.0.0', port=5000, debug=True)
except Exception as e:
    print(f"Error: {e}")
    input("Press Enter to exit...")
