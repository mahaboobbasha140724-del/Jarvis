import subprocess
import sys
import shutil
from pathlib import Path

def main():
    print("="*60)
    print(" BUILDING STANDALONE JARVIS WINDOWS DESKTOP APP")
    print("="*60)
    
    dist_dir = Path("dist")
    build_dir = Path("build")
    spec_file = Path("JARVIS.spec")
    
    if dist_dir.exists():
        print("Cleaning old dist directory...")
        shutil.rmtree(dist_dir)
    if build_dir.exists():
        print("Cleaning old build directory...")
        shutil.rmtree(build_dir)
    if spec_file.exists():
        print("Removing old spec file...")
        spec_file.unlink()

    # Build command - use onedir for reliability (avoids temp extraction crash)
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onedir",        # folder-based: stable, no temp extraction flash
        "--noconsole",
        "--name", "JARVIS",
        "--add-data", "templates;templates",
        "--add-data", "static;static",
        "--add-data", "core;core",
        "--add-data", "actions;actions",
        "--add-data", "memory;memory",
        "--add-data", "config;config",
        "--hidden-import", "sounddevice",
        "--hidden-import", "google.genai",
        "--hidden-import", "google.genai.types",
        "--hidden-import", "yfinance",
        "--hidden-import", "pyngrok",
        "--hidden-import", "pymongo",
        "--hidden-import", "dns",
        "--hidden-import", "webview",
        "--collect-all", "webview",
        "--collect-all", "sounddevice",
        "desktop_main.py"
    ]
    
    print("\nRunning PyInstaller compiler...")
    print("This may take 1-3 minutes...")
    try:
        subprocess.run(cmd, check=True)
        print("="*60)
        print(" BUILD COMPLETE SUCCESS!")
        print("="*60)
        print("Your standalone executable is ready in:")
        print(f"-> {dist_dir.resolve() / 'JARVIS.exe'}")
        print("="*60)
    except subprocess.CalledProcessError as e:
        print(f"Error compiling application: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
