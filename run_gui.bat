@echo off
setlocal
cd /d "%~dp0"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
  )
)

python "%~dp0gui_app.py"
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% neq 0 (
  echo.
  echo GUI exited with code: %EXIT_CODE%
  pause
)

exit /b %EXIT_CODE%
