@echo off
REM Launches the SpeechSwap Voice Conversion app. Assumes setup.bat has already
REM been run -- fails with a clear message rather than silently re-downloading
REM the checkpoint if it's missing.

setlocal

if not exist .venv (
    echo ERROR: no virtual environment found. Run setup.bat first.
    exit /b 1
)

set PYTHONIOENCODING=utf-8

.venv\Scripts\python.exe -c "import checkpoint_manager, sys; sys.exit(0 if checkpoint_manager.is_verified() else 1)"
if errorlevel 1 (
    echo ERROR: the voice-conversion model isn't downloaded/verified yet.
    echo Run setup.bat first, then try again.
    exit /b 1
)

echo Starting SpeechSwap Voice Conversion...
.venv\Scripts\python.exe -m streamlit run app.py
