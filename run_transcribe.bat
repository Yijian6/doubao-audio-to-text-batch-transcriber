@echo off
setlocal
cd /d "%~dp0"

if not exist "input" mkdir "input"
if not exist "output" mkdir "output"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
    echo Created config.json.
    echo Add your API key to config.json, then run this file again.
  ) else (
    echo Missing config.json.
    echo Create config.json in this folder:
    echo %~dp0
  )
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo Python was not found. Please install Python 3.11 or newer.
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

if "%DOUBAO_CLI_SMOKE_TEST%"=="1" (
  echo CLI startup check passed.
  exit /b 0
)

python "%~dp0doubao_batch_transcribe.py"
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
  echo Task finished.
) else (
  echo Task failed. Exit code: %EXIT_CODE%
)
pause
exit /b %EXIT_CODE%
