@echo off
REM Metra Timetable Bootstrap Script for Windows
REM Creates virtual environment and installs required packages

echo 🚂 Metra Timetable Bootstrap Script
echo ==================================

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Error: Python is not installed or not in PATH
    echo Please install Python and try again
    pause
    exit /b 1
)

for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VERSION=%%i
echo ✅ Found Python %PYTHON_VERSION%

REM Check if virtual environment already exists
if exist "venv" (
    echo ⚠️  Virtual environment already exists at .\venv
    set /p REPLY="Do you want to remove it and create a new one? (y/N): "
    if /i "%REPLY%"=="y" (
        echo 🗑️  Removing existing virtual environment...
        rmdir /s /q venv
    ) else (
        echo ℹ️  Using existing virtual environment
        goto :activate
    )
)

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo 📦 Creating virtual environment...
    python -m venv venv
    echo ✅ Virtual environment created
)

:activate
REM Activate virtual environment
echo 🔧 Activating virtual environment...
call venv\Scripts\activate.bat

REM Upgrade pip
echo ⬆️  Upgrading pip...
python -m pip install --upgrade pip

REM Install requirements
if exist "requirements.txt" (
    echo 📋 Installing packages from requirements.txt...
    pip install -r requirements.txt
    echo ✅ Packages installed successfully
) else (
    echo ⚠️  requirements.txt not found, installing basic packages...
    pip install pandas jinja2
    echo ✅ Basic packages installed
)

echo.
echo 🎉 Bootstrap complete!
echo.
echo To activate the virtual environment in the future, run:
echo   venv\Scripts\activate.bat
echo.
echo To get started:
echo   1. get-schedule.sh          # Download GTFS data (or run manually)
echo   2. python render-all-lines.py # Generate schedule data
echo   3. python -m http.server 8000 # Start web server
echo   4. Open http://localhost:8000/metra-interactive.html
echo.
echo Happy commuting! 🚂
pause