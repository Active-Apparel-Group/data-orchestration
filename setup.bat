@echo off
REM Data Orchestration Setup Script for Windows

echo Setting up Data Orchestration Pipeline...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.8+ and try again
    pause
    exit /b 1
)

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv
if %errorlevel% neq 0 (
    echo ERROR: Failed to create virtual environment
    pause
    exit /b 1
)

REM Activate virtual environment and install dependencies
echo Installing dependencies...
call venv\Scripts\activate.bat
pip install --upgrade pip
pip install -r requirements.txt

REM Check if .env exists, if not copy from example
if not exist .env (
    echo Creating .env file from template...
    copy .env.example .env
    echo.
    echo IMPORTANT: Please edit .env file with your database credentials
    echo.
)

echo.
echo Setup complete!
echo.
echo Next steps:
echo 1. Edit .env file with your database credentials
echo 2. Activate the environment: venv\Scripts\activate
echo 3. Start Kestra: make up
echo 4. Run tests: make test
echo.
pause
