@echo off
setlocal

cd /d "%~dp0backend"

if not exist ".deps\bin\uvicorn.exe" (
  echo Installing backend dependencies...
  python -m pip install --target .deps -r requirements.txt
)

".deps\bin\uvicorn.exe" app.main:app --host 127.0.0.1 --port 8000
