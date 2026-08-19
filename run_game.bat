@echo off
chcp 65001 >nul
echo Starting Pambaram: Spinning Top Battle Arena...
echo.
if exist ".venv\Scripts\python.exe" (
    echo Using virtual environment...
    ".venv\Scripts\python.exe" main.py
) else (
    echo Using system Python...
    python main.py
)
if errorlevel 1 (
    echo.
    echo Game crashed or closed with an error.
    echo If pygame is not installed, run install.bat first.
    pause
)
