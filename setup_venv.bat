@echo off

set VENV_DIR=venv

REM Check if venv exists
if not exist "%VENV_DIR%" (
    echo Virtual environment not found. Creating...
    python -m venv "%VENV_DIR%"
)

REM Activate venv
call "%VENV_DIR%\Scripts\activate.bat"

REM Upgrade pip
pip install --upgrade pip

REM Install packages (idempotent)
pip install mutagen
pip install librosa

REM tkinter is usually included in Windows Python by default
REM Done!
