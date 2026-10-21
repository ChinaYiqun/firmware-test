@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
if not exist "%~dp0.venv\Scripts\python.exe" (
  echo Prepared Python environment is missing. No installation will be attempted.
  pause
  exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0run_benchmark.py" %*
set "BENCH_EXIT=%ERRORLEVEL%"
echo.
echo Finished with exit code %BENCH_EXIT%.
pause
exit /b %BENCH_EXIT%
