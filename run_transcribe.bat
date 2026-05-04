@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist "input" mkdir "input"
if not exist "output" mkdir "output"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
    echo 已创建 config.json。
    echo 请先在 config.json 中填写 API Key，然后重新运行。
  ) else (
    echo 缺少 config.json。
    echo 请在这里创建 config.json：
    echo %~dp0
  )
  pause
  exit /b 1
)

where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.11 或更高版本。
  pause
  exit /b 1
)

python -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 11) else 1)"
if errorlevel 1 (
  echo 当前 Python 版本过低。请安装 Python 3.11 或更高版本。
  python --version
  pause
  exit /b 1
)

python "%~dp0doubao_batch_transcribe.py"
set EXIT_CODE=%ERRORLEVEL%

echo.
if %EXIT_CODE%==0 (
  echo 任务已完成。
) else (
  echo 任务失败，退出码：%EXIT_CODE%
)
pause
exit /b %EXIT_CODE%
