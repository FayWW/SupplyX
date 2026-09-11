@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "INSTALLER=%SCRIPT_DIR%install_daily_task.ps1"

if not exist "%INSTALLER%" (
    echo Task installer was not found: %INSTALLER%
    pause
    exit /b 1
)

powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%INSTALLER%"
if errorlevel 1 (
    echo.
    echo Failed to create the daily task.
    pause
    exit /b 1
)

echo.
echo Daily briefing task installed successfully.
echo It refreshes ai-news/index.html, sends notifications, and pushes to GitHub daily at 09:55.
echo Log: %SCRIPT_DIR%daily_news_task.log
echo Run now: schtasks /run /tn "DailyNewsBriefing"
pause
