@echo off
cd /d "%~dp0\.."
echo Starting Meeting AI Platform backend from: %CD%
echo API will be at: http://localhost:8000
echo Docs will be at: http://localhost:8000/docs
echo.
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
pause
