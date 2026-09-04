@echo off

set "SCRIPT_DIR=%~dp0"
set "NEWS_PY=%SCRIPT_DIR%news.py"

if not exist "%NEWS_PY%" (
    for %%f in ("%SCRIPT_DIR%news*.py") do (
        set "NEWS_PY=%%f"
    )
)

echo.
echo  ============================================
echo   Setup Daily News Briefing Task
echo  ============================================
echo.
echo   Script: %NEWS_PY%
echo   Time:   09:55 every day
echo.

schtasks /delete /tn "DailyNewsBriefing" /f >nul 2>&1

schtasks /create /tn "DailyNewsBriefing" /tr "python \"%NEWS_PY%\" --once" /sc daily /st 09:55 /f

if %errorlevel% equ 0 (
    echo.
    echo  ============================================
    echo   SUCCESS!
    echo  ============================================
    echo.
    echo   The system will run news briefing at 09:55 daily
    echo   and send email to your Outlook inbox.
    echo.
    echo   Note: PC must be ON at 09:55
    echo.
    echo   Commands:
    echo   - Check:  schtasks /query /tn "DailyNewsBriefing"
    echo   - Delete: schtasks /delete /tn "DailyNewsBriefing" /f
    echo   - Run now: schtasks /run /tn "DailyNewsBriefing"
    echo.
) else (
    echo.
    echo   FAILED! Please right-click this file
    echo   and select "Run as administrator"
    echo.
)

pause
