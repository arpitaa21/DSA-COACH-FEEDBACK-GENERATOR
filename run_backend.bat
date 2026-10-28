@echo off
echo ====================================================
echo Starting DSA Coach Backend (FastAPI + Code Exec Agent)
echo ====================================================
cd /d "%~dp0backend"

if exist "venv\Scripts\python.exe" (
    echo Using virtualenv Python (Python 3.11)...
    "venv\Scripts\python.exe" -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
) else (
    echo Using system Python...
    python -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
)
pause
