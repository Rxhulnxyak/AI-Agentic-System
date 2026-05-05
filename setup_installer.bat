@echo off
echo ==========================================
echo    Kolimarii AI Assistant Installer
echo ==========================================
echo.

echo [1/3] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo Error: Python is not installed. Please install Python 3.10+
    pause
    exit /b
)

echo [2/3] Installing dependencies...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo Error: Failed to install dependencies.
    pause
    exit /b
)

echo [3/3] Setting up environment...
if not exist .env (
    copy .env.example .env
    echo Created .env file. Please add your API keys.
)

echo.
echo ==========================================
echo    Installation Complete!
echo    Run 'python main.py' to start.
echo ==========================================
pause
