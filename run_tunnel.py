import sys
import os
from pathlib import Path

def main():
    try:
        from pyngrok import ngrok, conf
    except ImportError:
        print("Error: pyngrok not installed. Run: pip install pyngrok")
        sys.exit(1)

    config_path = Path("config/api_keys.json")
    auth_token = ""
    
    if config_path.exists():
        try:
            import json
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
                auth_token = config.get("ngrok_auth_token", "").strip()
        except Exception:
            pass

    if not auth_token:
        print("="*60)
        print(" NGROK AUTH TOKEN REQUIRED")
        print("="*60)
        print("1. Sign up for a free account at: https://dashboard.ngrok.com")
        print("2. Copy your Auth Token from the 'Your Authtoken' section.")
        print("3. Enter your Auth Token below:")
        auth_token = input("> ").strip()
        if not auth_token:
            print("Error: Auth Token cannot be empty.")
            sys.exit(1)

        try:
            import json
            config = {}
            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    config = json.load(f)
            config["ngrok_auth_token"] = auth_token
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=4)
            print("Saved Auth Token to config/api_keys.json!")
        except Exception as e:
            print(f"Warning: Could not save config file: {e}")

    conf.get_default().auth_token = auth_token
    
    print("\nStarting ngrok tunnel to port 8000...")
    try:
        tunnel = ngrok.connect(8000, "http")
        print("="*60)
        print(" TUNNEL ESTABLISHED SUCCESSFULLY!")
        print("="*60)
        print(f"Public HTTPS URL: {tunnel.public_url}")
        print("Open this URL on your phone or remote browser to connect to JARVIS.")
        print("Press Ctrl+C to stop the tunnel.")
        print("="*60)
        
        import time
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nStopping tunnel...")
        ngrok.kill()
    except Exception as e:
        print(f"\nFailed to start tunnel: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
