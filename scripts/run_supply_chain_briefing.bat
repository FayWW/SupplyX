@echo off
setlocal
cd /d "%~dp0.."
"C:\Users\wanhui2\AppData\Local\Programs\Python\Python314\python.exe" scripts\refresh_and_publish_supply_chain_briefing.py
exit /b %errorlevel%