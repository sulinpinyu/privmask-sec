@echo off
setlocal
cd /d "%~dp0"

rem Prefer the Python installed by the user
set "PY=E:\Dev\Python313\python.exe"

rem Fallback 1: bundled Python
if not exist "%PY%" set "PY=%USERPROFILE%\.workbuddy\binaries\python\versions\3.13.12\python.exe"

rem Fallback 2: whatever is on PATH
if not exist "%PY%" set "PY=python"

"%PY%" -c "import sys" >nul 2>nul
if errorlevel 1 (
    echo.
    echo [ERROR] Python not found or broken.
    echo Please install Python 3.9+ from https://www.python.org/downloads/
    echo IMPORTANT: check "Add python.exe to PATH" during installation.
    echo.
    goto :end
)

echo ============================================================
echo  STEP 1 - ANALYZE: find sensitive info in examples/sample.txt
echo ============================================================
echo.
"%PY%" cli.py analyze -f examples/sample.txt
echo.
echo ============================================================
echo  STEP 2 - MASK: mask sensitive info in examples/access.log
echo ============================================================
echo.
"%PY%" cli.py mask -f examples/access.log -s mask
echo.

:end
if not defined PRIVMASK_NOPAUSE pause
endlocal
