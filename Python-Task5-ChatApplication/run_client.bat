@echo off
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m client.gui %*
) else (
    python -m client.gui %*
)
if errorlevel 1 pause
