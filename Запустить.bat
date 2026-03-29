@echo off
title Supend Messenger

set "TRACKER=caboose.proxy.rlwy.net:48109"
set "DIR=%~dp0"

echo === Supend Messenger ===
echo.

echo Installing dependencies...
python -m pip install PyNaCl aiohttp aioconsole --quiet --disable-pip-version-check

echo Starting...
cd /d "%DIR%"
start "" "http://127.0.0.1:8765"
timeout /t 3 /nobreak >nul
python main.py --gui --no-history --tracker "%TRACKER%"

pause
