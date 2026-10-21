@echo off
setlocal
set "PYTHONIOENCODING=utf-8"
set "BENCH_RUN_PY=%~dp0..\2026-10-20-opus5-harness-comparison\.venv\Scripts\python.exe"
if not exist "%BENCH_RUN_PY%" (
  echo Prepared Python environment is missing. Follow README environment setup first.
  pause
  exit /b 1
)
"%BENCH_RUN_PY%" "%~dp0run_full.py" %*
set "BENCH_EXIT=%ERRORLEVEL%"
echo.
echo Finished with exit code %BENCH_EXIT%.
pause
exit /b %BENCH_EXIT%
