@echo off
REM 快速启动（开发/本地）
REM 在项目根目录执行: scripts\start.bat  或  cd 到项目根后  python -m uvicorn src.main:app --reload --port 8000

cd /d "%~dp0.."
echo Starting server at http://127.0.0.1:8000
echo Press Ctrl+C to stop.
python -m uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
