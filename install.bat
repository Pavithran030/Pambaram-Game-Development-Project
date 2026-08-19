@echo off
chcp 65001 >nul
setlocal
set SCRIPT_DIR=%~dp0
pushd "%SCRIPT_DIR%"
echo ============================================
echo   Pambaram: Spinning Top Battle Arena
echo   Setup & Installer for Windows
echo ============================================
echo.

echo [1/5] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH.
    echo Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)
python --version
echo OK - Python found.
echo.

echo [2/5] Creating virtual environment (.venv)...
if exist ".venv\Scripts\python.exe" (
    echo Virtual environment already exists, skipping creation.
) else (
    python -m venv .venv
    if errorlevel 1 (
        echo WARNING: venv creation failed, falling back to system install.
        goto SYSTEM_INSTALL
    )
    echo OK - Virtual environment created at .venv
)
set VENV_PY=%SCRIPT_DIR%.venv\Scripts\python.exe
echo.

echo [3/5] Upgrading pip in venv...
"%VENV_PY%" -m pip install --upgrade pip --quiet --no-warn-script-location 2>nul
echo.

echo [4/5] Installing project dependencies into virtual environment...
"%VENV_PY%" -m pip install -r requirements.txt --quiet --no-warn-script-location
if errorlevel 1 (
    echo WARNING: Virtual env install failed. Trying system install...
    goto SYSTEM_INSTALL
)
echo OK - Dependencies installed in .venv
echo.

echo [5/5] Verifying pygame installation...
"%VENV_PY%" -c "import pygame; print(f'Pygame version: {pygame.__version__}')"
if errorlevel 1 (
    echo ERROR: Pygame could not be imported. Trying system install...
    goto SYSTEM_INSTALL
)
goto DONE

:SYSTEM_INSTALL
echo.
echo ============================================
echo   Performing system-wide fallback install
echo ============================================
echo.
echo [B/3] Installing dependencies to system Python...
python -m pip install -r requirements.txt --quiet
if errorlevel 1 (
    echo Trying user-mode install...
    python -m pip install --user -r requirements.txt --quiet
    if errorlevel 1 (
        echo.
        echo ERROR: Failed to install dependencies.
        echo Try running this script as Administrator.
        pause
        exit /b 1
    )
)
echo OK - Dependencies installed successfully.
echo.

echo [C/3] Verifying pygame installation...
python -c "import pygame; print(f'Pygame version: {pygame.__version__}')"
if errorlevel 1 (
    echo ERROR: Pygame could not be imported.
    pause
    exit /b 1
)
goto DONE

:DONE
echo.
echo ============================================
echo   Setup complete!
echo.
echo   To play the game:
echo   - Double-click 'run_game.bat'
echo   - OR run: .venv\Scripts\python.exe main.py
echo ============================================
echo.
popd
endlocal
pause
