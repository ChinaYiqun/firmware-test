@echo off
setlocal
powershell.exe -NoProfile -ExecutionPolicy Bypass -File "%~dp0start.ps1" -ResumeLatest %*
set "RESULT=%errorlevel%"
echo.
echo Exit code: %RESULT%
pause
exit /b %RESULT%
