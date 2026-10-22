@echo off
setlocal
set "PYTHON=%~dp0..\2026-10-20-opus5-harness-comparison\.venv\Scripts\python.exe"
if not exist "%PYTHON%" (
  echo Missing Python environment. See the root README for setup.
  exit /b 1
)
"%PYTHON%" "%~dp0run_benchmark.py" %*
exit /b %errorlevel%
