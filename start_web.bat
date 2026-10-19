@echo off
setlocal
cd /d "%~dp0"

set "PY=E:\Dev\Python313\python.exe"
if not exist "%PY%" set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"
if not exist "%PY%" set "PY=python"

"%PY%" -c "import flask" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Flask is not installed.
    echo Run this command first:
    echo     E:\Dev\Python313\python.exe -m pip install flask
    echo.
    goto :end
)

echo ============================================================
echo   privmask web server
echo   Browser opens in 3 seconds, or visit:
echo   http://127.0.0.1:5000
echo   Press Ctrl+C to stop
echo ============================================================
echo.

start "" cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5000"
"%PY%" server.py

:end
if not defined PRIVMASK_NOPAUSE pause
endlocal
