@echo off
REM Double-click this file from the meeting_AI_platform root folder.
cd /d "%~dp0"
echo Starting Meeting AI Platform backend from: %CD%
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
pause
