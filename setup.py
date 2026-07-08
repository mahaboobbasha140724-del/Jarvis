import subprocess
import sys
import traceback
import os

def main():
    print("="*60)
    print(" J.A.R.V.I.S Installation Setup Wizard")
    print("="*60)
    
    try:
        if not os.path.exists("requirements.txt"):
            print("Error: requirements.txt not found in current folder.")
            print("Please make sure you run setup.py from the project root folder.")
            return

        print("\n[1/2] Installing requirements from requirements.txt...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"], check=True)
        
        print("\n[2/2] Installing Playwright browsers...")
        subprocess.run([sys.executable, "-m", "playwright", "install"], check=True)
        
        print("\n" + "="*60)
        print("  SETUP COMPLETE SUCCESS!")
        print("="*60)
        print("Run 'python web_main.py' to start the JARVIS web interface.")
        print("Run 'python main.py' to start the command line engine.")
        print("Created by Roshab Bhandari.")
        print("="*60)
        
    except Exception as e:
        print("\n" + "="*60)
        print("   INSTALLATION FAILED")
        print("="*60)
        traceback.print_exc()
        print("="*60)
        print("\nPlease resolve the error above and try running setup.py again.")

if __name__ == "__main__":
    main()
    input("\nPress Enter to exit...")
