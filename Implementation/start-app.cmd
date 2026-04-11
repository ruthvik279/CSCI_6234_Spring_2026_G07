@echo off
setlocal

cd /d "%~dp0"

start "Code Review Backend" cmd /k "%~dp0run-backend.cmd"
start "Code Review Frontend" cmd /k "%~dp0run-frontend.cmd"
