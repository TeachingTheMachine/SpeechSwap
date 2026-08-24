@echo off
REM SpeechSwap Voice Conversion -- first-time setup.
REM Creates the venv, installs pinned dependencies, checks for ffmpeg, and
REM downloads + verifies the pinned OpenVoice checkpoint so Demo Mode works
REM immediately after this completes (not on the app's first run).

setlocal

echo === SpeechSwap Voice Conversion: Setup ===

where ffmpeg >nul 2>nul
if errorlevel 1 (
    echo ERROR: ffmpeg was not found on PATH.
    echo Install ffmpeg and ensure it is on PATH, then re-run this script.
    exit /b 1
)
echo ffmpeg found.

if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
)

echo Installing pinned dependencies...
.venv\Scripts\python.exe -m pip install --quiet --upgrade pip
.venv\Scripts\python.exe -m pip install --quiet -r requirements.txt
if errorlevel 1 (
    echo ERROR: dependency install failed.
    exit /b 1
)

echo Downloading and verifying the pinned voice-conversion model...
set PYTHONIOENCODING=utf-8
.venv\Scripts\python.exe checkpoint_manager.py
if errorlevel 1 (
    echo ERROR: checkpoint download/verification failed.
    exit /b 1
)

echo.
echo === Setup complete. Run run_demo.bat to start the app. ===
