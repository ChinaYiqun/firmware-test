@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" %*
set "RESULT=%errorlevel%"
echo.
echo Exit code: %RESULT%
pause
exit /b %RESULT%
