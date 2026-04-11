@echo off
setlocal

cd /d "%~dp0frontend"

if not exist "node_modules" (
  echo Installing frontend dependencies...
  npm.cmd install
)

npm.cmd run dev -- --host 127.0.0.1 --port 5173
