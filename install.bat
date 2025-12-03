@echo off
echo ========================================
echo MT5 Multi-Account Automation - Setup
echo ========================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python is not installed or not in PATH
    echo Please install Python 3.8+ from https://www.python.org/downloads/
    pause
    exit /b 1
)

echo [INFO] Python is installed
python --version
echo.

REM Check if pip is available
pip --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] pip is not available
    pause
    exit /b 1
)

echo [INFO] pip is available
echo.

REM Install requirements
echo [INFO] Installing Python dependencies...
echo.
pip install -r requirements.txt

if errorlevel 1 (
    echo.
    echo [ERROR] Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo ========================================
echo [SUCCESS] Installation Complete!
echo ========================================
echo.

REM Check if config.py exists, if not create from example
if not exist config.py (
    if exist config.example.py (
        echo [INFO] Creating config.py from example...
        copy config.example.py config.py >nul
        echo [SUCCESS] config.py created!
        echo [ACTION REQUIRED] Please edit config.py with your account details
    ) else (
        echo [WARNING] config.example.py not found
    )
) else (
    echo [INFO] config.py already exists
)

echo.
echo Next steps:
echo 1. Edit config.py to add your MT5 accounts and settings
echo 2. Setup MongoDB (local or Atlas)
echo 3. Run: python main.py
echo.
echo For detailed setup instructions, see SETUP_GUIDE.md
echo.
pause

