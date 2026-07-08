import sys
import os
import time
import threading
import socket
import traceback
from pathlib import Path

def show_error_popup(title, message):
    try:
        import ctypes
        ctypes.windll.user32.MessageBoxW(0, str(message), str(title), 0x10) # 0x10 is MB_ICONERROR
    except Exception:
        pass

def main():
    try:
        if getattr(sys, "frozen", False):
            base_dir = Path(sys._MEIPASS)
            log_dir = Path(sys.executable).parent
        else:
            base_dir = Path(__file__).resolve().parent
            log_dir = base_dir

        sys.path.append(str(base_dir))

        import webview
        import uvicorn
        from web_main import app

        def is_port_in_use(port):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                return s.connect_ex(('127.0.0.1', port)) == 0

        def start_server():
            try:
                uvicorn.run(app, host="127.0.0.1", port=8000, log_level="error", access_log=False)
            except Exception as e:
                with open(log_dir / "server_error.log", "w", encoding="utf-8") as f:
                    f.write(traceback.format_exc())

        if not is_port_in_use(8000):
            t = threading.Thread(target=start_server, daemon=True)
            t.start()
            time.sleep(1.5)

        webview.create_window(
            title="J.A.R.V.I.S: Arc Reactor Dashboard",
            url="http://127.0.0.1:8000",
            width=1360,
            height=768,
            min_size=(1024, 768),
            resizable=True
        )
        webview.start()

    except Exception as e:
        err_msg = traceback.format_exc()
        try:
            if getattr(sys, "frozen", False):
                err_log_path = Path(sys.executable).parent / "error.log"
            else:
                err_log_path = Path(__file__).resolve().parent / "error.log"
            with open(err_log_path, "w", encoding="utf-8") as f:
                f.write(err_msg)
        except Exception:
            pass
            
        show_error_popup("J.A.R.V.I.S Startup Error", f"JARVIS failed to launch.\n\nError details:\n{e}\n\nA detailed error log has been written to: error.log")
        sys.exit(1)

if __name__ == "__main__":
    main()
