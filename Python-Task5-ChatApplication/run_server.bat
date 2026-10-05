@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m server.server %*
) else (
    python -m server.server %*
)
if errorlevel 1 pause
