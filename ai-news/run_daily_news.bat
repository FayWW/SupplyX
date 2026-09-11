@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PYTHON_EXE=%LocalAppData%\Programs\Python\Python314\python.exe"
set "NEWS_PY=%SCRIPT_DIR%news.py"
set "LOG_FILE=%SCRIPT_DIR%daily_news_task.log"

if not exist "%PYTHON_EXE%" (
    for /f "delims=" %%p in ('where python 2^>nul') do (
        set "PYTHON_EXE=%%p"
        goto :run_news
    )
)

:run_news
"%PYTHON_EXE%" "%NEWS_PY%" >> "%LOG_FILE%" 2>&1
exit /b %errorlevel%