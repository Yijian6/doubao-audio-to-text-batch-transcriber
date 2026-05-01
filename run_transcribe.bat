@echo off
setlocal
cd /d "%~dp0"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
    echo Created config.json from config.example.json
    echo Edit config.json and add your API key, then run again.
  ) else (
    echo Missing config.json
    echo Copy or create config.json in:
    echo %~dp0
  )
  pause
  exit /b 1
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
