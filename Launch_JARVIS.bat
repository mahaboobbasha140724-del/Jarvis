@echo off
setlocal
set "JARVIS_DIR=%~dp0"
cd /d "%JARVIS_DIR%"
start "" "%JARVIS_DIR%JARVIS\JARVIS.exe"
endlocal
