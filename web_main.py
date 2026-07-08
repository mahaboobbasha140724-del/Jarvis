import asyncio
import json
import os
import sys
import warnings
warnings.filterwarnings("ignore")
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
import threading
import time
from pathlib import Path
from typing import Set

import uvicorn
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse

# Add current directory to path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Import core JARVIS logic
import main
from ui import _SysMetrics

app = FastAPI(title="JARVIS Web Interface")

# Global active connections
active_connections: Set[WebSocket] = set()
metrics_collector = _SysMetrics()

# Global state for Web UI shim
class WebJarvisUI:
    def __init__(self):
        self._ready = False
        self._on_text_command = None
        self._current_file_path = None
        self.state = "OFFLINE"
        self.logs_history = []
        self.loop = None

        # Check if config exists on startup
        if self._check_api_keys():
            self._ready = True
            self.write_log("SYS: API keys detected. Connecting to Gemini Live...")
        else:
            self.write_log("SYS: JARVIS is offline. Please enter your Gemini & OpenRouter keys in the 'System Parameters' panel to connect.")

    def _check_api_keys(self) -> bool:
        if not main.API_CONFIG_PATH.exists():
            return False
        try:
            with open(main.API_CONFIG_PATH, "r", encoding="utf-8") as f:
                d = json.load(f)
                return bool(d.get("gemini_api_key")) and bool(d.get("openrouter_api_key"))
        except Exception:
            return False

    @property
    def muted(self) -> bool:
        return False

    @muted.setter
    def muted(self, v: bool):
        pass

    @property
    def current_file(self) -> str | None:
        return self._current_file_path

    @property
    def on_text_command(self):
        return self._on_text_command

    @on_text_command.setter
    def on_text_command(self, cb):
        self._on_text_command = cb

    def wait_for_api_key(self):
        while not self._ready:
            time.sleep(0.1)

    def set_state(self, state: str):
        self.state = state
        self.broadcast({"type": "state", "state": state})

    def write_log(self, text: str):
        print(text)
        self.logs_history.append(text)
        if len(self.logs_history) > 200:
            self.logs_history.pop(0)
        self.broadcast({"type": "log", "text": text})

    def start_speaking(self):
        self.set_state("SPEAKING")

    def stop_speaking(self):
        self.set_state("LISTENING")

    def broadcast(self, data: dict):
        if not active_connections:
            return
        
        msg = json.dumps(data)
        async def send_to_all():
            for websocket in list(active_connections):
                try:
                    await websocket.send_text(msg)
                except Exception:
                    if websocket in active_connections:
                        active_connections.remove(websocket)
        
        if self.loop and self.loop.is_running():
            asyncio.run_coroutine_threadsafe(send_to_all(), self.loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(send_to_all())
                else:
                    asyncio.run(send_to_all())
            except Exception:
                # Fallback to run in a separate thread if no event loop in current context
                threading.Thread(target=lambda: asyncio.run(send_to_all()), daemon=True).start()

# Global UI Instance
ui_instance = WebJarvisUI()

# Setup static files directory
static_dir = BASE_DIR / "static"
static_dir.mkdir(exist_ok=True)

# Copy face.png to static if it exists
face_src = BASE_DIR / "face.png"
face_dst = static_dir / "face.png"
if face_src.exists() and not face_dst.exists():
    try:
        face_dst.write_bytes(face_src.read_bytes())
    except Exception as e:
        print(f"Error copying face.png to static: {e}")

app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

@app.get("/", response_class=HTMLResponse)
async def get_index():
    template_path = BASE_DIR / "templates" / "index.html"
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return "<h3>Error: templates/index.html not found.</h3>"

@app.post("/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        uploads_dir = BASE_DIR / "uploads"
        uploads_dir.mkdir(exist_ok=True)
        
        file_path = uploads_dir / file.filename
        content = await file.read()
        file_path.write_bytes(content)
        
        ui_instance._current_file_path = str(file_path.resolve())
        return JSONResponse({"status": "success", "filepath": ui_instance._current_file_path})
    except Exception as e:
        return JSONResponse({"status": "error", "message": str(e)}, status_code=500)

@app.post("/remove-file")
async def remove_file():
    ui_instance._current_file_path = None
    return JSONResponse({"status": "success"})

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.add(websocket)
    
    # Send current configs if exists
    config_data = {}
    if main.API_CONFIG_PATH.exists():
        try:
            with open(main.API_CONFIG_PATH, "r", encoding="utf-8") as f:
                config_data = json.load(f)
        except Exception:
            pass
    
    await websocket.send_json({
        "type": "config",
        "gemini_api_key": config_data.get("gemini_api_key", ""),
        "openrouter_api_key": config_data.get("openrouter_api_key", ""),
        "os_system": config_data.get("os_system", "Windows"),
        "dhan_client_id": config_data.get("dhan_client_id", ""),
        "dhan_access_token": config_data.get("dhan_access_token", "")
    })

    # Send state and existing logs
    await websocket.send_json({"type": "state", "state": ui_instance.state})
    for log in ui_instance.logs_history:
        await websocket.send_json({"type": "log", "text": log})

    try:
        while True:
            data = await websocket.receive_text()
            payload = json.loads(data)
            
            if payload.get("type") == "command":
                cmd_text = payload.get("text", "").strip()
                if cmd_text:
                    ui_instance.write_log(f"You: {cmd_text}")
                    if ui_instance.on_text_command:
                        # Run callback in background thread
                        threading.Thread(
                            target=ui_instance.on_text_command,
                            args=(cmd_text,),
                            daemon=True
                        ).start()
                    else:
                        ui_instance.write_log("SYS: JARVIS is offline. Please configure your API keys first to enable interaction.")
            
            elif payload.get("type") == "save_config":
                gemini = payload.get("gemini_api_key", "").strip()
                openrouter = payload.get("openrouter_api_key", "").strip()
                os_name = payload.get("os_system", "Windows").strip()
                dhan_client_id = payload.get("dhan_client_id", "").strip()
                dhan_access_token = payload.get("dhan_access_token", "").strip()
                
                main.API_CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
                
                # Load existing config to avoid overwriting Dhan keys with empty string
                existing = {}
                if main.API_CONFIG_PATH.exists():
                    try:
                        with open(main.API_CONFIG_PATH, "r", encoding="utf-8") as f:
                            existing = json.load(f)
                    except Exception:
                        pass
                
                new_config = {
                    "gemini_api_key": gemini or existing.get("gemini_api_key", ""),
                    "openrouter_api_key": openrouter or existing.get("openrouter_api_key", ""),
                    "os_system": os_name,
                    "dhan_client_id": dhan_client_id or existing.get("dhan_client_id", ""),
                    "dhan_access_token": dhan_access_token or existing.get("dhan_access_token", "")
                }
                with open(main.API_CONFIG_PATH, "w", encoding="utf-8") as f:
                    json.dump(new_config, f, indent=4)
                
                ui_instance._ready = True
                ui_instance.write_log("SYS: Configuration updated successfully.")
                
    except WebSocketDisconnect:
        active_connections.remove(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        if websocket in active_connections:
            active_connections.remove(websocket)

# Background task to broadcast system metrics
async def broadcast_metrics_loop():
    while True:
        try:
            if active_connections:
                cpu = metrics_collector.cpu
                mem = metrics_collector.mem
                net = metrics_collector.net
                
                msg = json.dumps({
                    "type": "metrics",
                    "cpu": cpu,
                    "mem": mem,
                    "net": net
                })
                
                for websocket in list(active_connections):
                    try:
                        await websocket.send_text(msg)
                    except Exception:
                        if websocket in active_connections:
                            active_connections.remove(websocket)
        except Exception as e:
            print(f"Metrics broadcast error: {e}")
        await asyncio.sleep(2)

# Start metrics loop in event loop
@app.on_event("startup")
async def startup_event():
    ui_instance.loop = asyncio.get_running_loop()
    asyncio.create_task(broadcast_metrics_loop())
    # Start JARVIS engine in a separate daemon thread
    threading.Thread(target=run_jarvis_engine, daemon=True).start()

def run_jarvis_engine():
    ui_instance.wait_for_api_key()
    jarvis = main.JarvisLive(ui_instance)
    try:
        asyncio.run(jarvis.run())
    except KeyboardInterrupt:
        print("\n[JARVIS] Shutting down JARVIS engine...")
    except Exception as e:
        print(f"JARVIS Engine Error: {e}")

if __name__ == "__main__":
    # Run FastAPI web server (blocking main thread)
    print("Starting JARVIS Web Server on http://localhost:8000 ...")
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
