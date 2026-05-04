@echo off
setlocal
chcp 65001 >nul
cd /d "%~dp0"

if not exist "input" mkdir "input"
if not exist "output" mkdir "output"

if not exist "config.json" (
  if exist "config.example.json" (
    copy /Y "config.example.json" "config.json" >nul
    echo 已创建 config.json
  ) else (
    echo 缺少 config.example.json，无法创建默认配置。
    pause
    exit /b 1
  )
)

where python >nul 2>nul
if errorlevel 1 (
  echo 未找到 Python。请先安装 Python 3.11 或更高版本。
  echo 下载地址：https://www.python.org/downloads/
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

python "%~dp0gui_app.py"
set EXIT_CODE=%ERRORLEVEL%

if %EXIT_CODE% neq 0 (
  echo.
  echo GUI 运行失败，退出码：%EXIT_CODE%
  pause
)

exit /b %EXIT_CODE%
