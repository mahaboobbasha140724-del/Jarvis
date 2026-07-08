import subprocess
import sys
import zipfile
import shutil
from pathlib import Path

def create_installer_zip():
    """Creates a distributable zip of the onedir build."""
    dist_folder = Path("dist/JARVIS")
    if not dist_folder.exists():
        print("ERROR: dist/JARVIS folder not found. Run build_desktop.py first.")
        sys.exit(1)

    # Add config skeleton
    config_out = dist_folder / "config"
    config_out.mkdir(exist_ok=True)
    import json
    default_config = {
        "gemini_api_key": "",
        "openrouter_api_key": "",
        "os_system": "Windows",
        "dhan_client_id": "",
        "dhan_access_token": "",
        "ngrok_auth_token": ""
    }
    with open(config_out / "api_keys.json", "w", encoding="utf-8") as f:
        json.dump(default_config, f, indent=4)

    # Copy launcher bat into dist
    bat_src = Path("Launch_JARVIS.bat")
    if bat_src.exists():
        shutil.copy(bat_src, dist_folder.parent / "Launch_JARVIS.bat")

    # Create zip
    zip_path = Path("JARVIS_Software.zip")
    print(f"Creating {zip_path}...")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as zf:
        for f in sorted(dist_folder.parent.rglob("*")):
            if f.is_file():
                arcname = f.relative_to(dist_folder.parent.parent)
                zf.write(f, arcname)

    size_mb = zip_path.stat().st_size / (1024 * 1024)
    print(f"\nDone! JARVIS_Software.zip created: {size_mb:.1f} MB")
    print(f"Location: {zip_path.resolve()}")
    print("\nTo install on any Windows PC:")
    print("  1. Extract the zip")
    print("  2. Double-click JARVIS.exe inside the JARVIS folder")
    print("  OR right-click JARVIS.exe > Send to > Desktop (create shortcut)")

if __name__ == "__main__":
    create_installer_zip()
