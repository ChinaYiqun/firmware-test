@echo off
"%~dp0..\2026-10-20-opus5-harness-comparison\.venv\Scripts\python.exe" "%~dp0..\2026-10-20-opus5-harness-comparison\run_benchmark.py" --experiment-dir "%~dp0." %*
pause
