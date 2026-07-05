"""
shell_executor.py — Runs any terminal/shell command for JARVIS
Supports: PowerShell, CMD, Python one-liners, system commands
"""
import subprocess
import sys
import os
import json
from pathlib import Path

def shell_executor(parameters=None, player=None, **kwargs):
    """
    Execute any shell command and return its output.
    parameters: dict with keys:
        command (str)  — the command to run
        shell   (str)  — 'powershell' | 'cmd' | 'auto' (default: auto)
        cwd     (str)  — working directory (default: user home)
        timeout (int)  — timeout in seconds (default: 30)
        silent  (bool) — don't read stdout back (default: False)
    """
    if isinstance(parameters, str):
        parameters = {"command": parameters}
    if not isinstance(parameters, dict):
        return "Error: No command provided."

    command  = parameters.get("command", "").strip()
    shell    = parameters.get("shell", "auto").lower()
    cwd      = parameters.get("cwd", None) or str(Path.home())
    timeout  = int(parameters.get("timeout", 30))
    silent   = parameters.get("silent", False)

    if not command:
        return "Error: Empty command string."

    print(f"[ShellExecutor] Running: {command}")
    if player:
        player.write_log(f"[JARVIS] Executing: {command}")

    try:
        # Determine shell
        if shell == "powershell" or (shell == "auto" and sys.platform == "win32"):
            full_cmd = ["powershell", "-NoProfile", "-NonInteractive",
                        "-ExecutionPolicy", "Bypass", "-Command", command]
        elif shell == "cmd":
            full_cmd = ["cmd", "/c", command]
        else:
            # Linux/macOS bash
            full_cmd = ["/bin/bash", "-c", command]

        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=cwd,
            encoding="utf-8",
            errors="replace"
        )

        stdout = result.stdout.strip()
        stderr = result.stderr.strip()
        retcode = result.returncode

        if silent:
            return f"Command executed. Return code: {retcode}."

        # Build response
        output_parts = []
        if stdout:
            # Truncate very long output
            lines = stdout.split("\n")
            if len(lines) > 50:
                output_parts.append("\n".join(lines[:50]))
                output_parts.append(f"... [{len(lines)-50} more lines truncated]")
            else:
                output_parts.append(stdout)

        if stderr and retcode != 0:
            output_parts.append(f"\nSTDERR: {stderr[:500]}")

        output = "\n".join(output_parts) if output_parts else "(no output)"

        if retcode == 0:
            summary = f"[JARVIS] Command completed successfully.\n{output}"
        else:
            summary = f"[JARVIS] Command exited with code {retcode}.\n{output}"

        if player:
            # Log first 2 lines to UI
            preview = "\n".join(output.split("\n")[:3])
            player.write_log(f"[Shell] {preview}")

        return summary

    except subprocess.TimeoutExpired:
        return f"Error: Command timed out after {timeout} seconds."
    except FileNotFoundError as e:
        return f"Error: Command not found — {e}"
    except Exception as e:
        return f"Error running command: {str(e)}"
