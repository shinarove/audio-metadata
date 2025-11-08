#!/usr/bin/env bash

@echo off

set VENV_DIR=venv

REM Check if venv exists
if not exist "%VENV_DIR%" (
    call "setup_venv.bat"
) else (
	REM Activate venv, when found
	call "%VENV_DIR%\Scripts\activate.bat"
)

REM Run metadata skript
python metadata.py
