import sys
import os
import time
import threading
import socket
import webview
import uvicorn
from pathlib import Path

# Add current directory to path
if getattr(sys, "frozen", False):
    base_dir = Path(sys._MEIPASS)
else:
    base_dir = Path(__file__).resolve().parent

sys.path.append(str(base_dir))

from web_main import app

def is_port_in_use(port):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error", access_log=False)

def main():
    if not is_port_in_use(8000):
        t = threading.Thread(target=start_server, daemon=True)
        t.start()
        time.sleep(1.0)
        
    print("Launching J.A.R.V.I.S Desktop interface...")
    webview.create_window(
        title="J.A.R.V.I.S: Arc Reactor Dashboard",
        url="http://127.0.0.1:8000",
        width=1360,
        height=768,
        min_size=(1024, 768),
        resizable=True
    )
    webview.start()

if __name__ == "__main__":
    main()
