@echo off
setlocal
cd /d "%~dp0"

if not exist "input" mkdir "input"
if not exist "output" mkdir "output"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
    echo Created config.json
  ) else (
    echo Missing config.example.json. Cannot create default config.
    pause
    exit /b 1
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Please install Python 3.11 or newer.
  echo https://www.python.org/downloads/
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo Python is too old. Please install Python 3.11 or newer.
  python --version
  pause
  exit /b 1
)

if "%DOUBAO_GUI_SMOKE_TEST%"=="1" (
  echo GUI startup check passed.
  exit /b 0
)

python "%~dp0gui_app.py"
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% neq 0 (
  echo.
  echo GUI failed. Exit code: %EXIT_CODE%
  pause
)

exit /b %EXIT_CODE%
