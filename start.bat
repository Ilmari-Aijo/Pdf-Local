@echo off
rem Starts PDF Local at http://127.0.0.1:5050 (only reachable from this computer).
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Creating the virtual environment for the first time...
  python -m venv .venv || goto :error
  ".venv\Scripts\python.exe" -m pip install --upgrade pip
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt || goto :error
)
start "" "http://127.0.0.1:5050"
".venv\Scripts\python.exe" app.py
goto :eof
:error
echo Could not set up the environment. Make sure Python is installed.
pause
