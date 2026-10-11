@echo off
cd /d "%~dp0"

rem 让 Python 用 GBK 输出，否则中文提示在 cmd 窗口里会乱码
set PYTHONIOENCODING=gbk

rem 选择可用的 Python（优先官方 launcher，其次 PATH 里的 python）
set "PY=py -3"
%PY% -c "import markdown" >nul 2>&1
if errorlevel 1 set "PY=python"

echo ================================================
echo   本地预览（不会上传，只在你电脑上看）
echo ================================================
echo.

echo [1/2] 构建网站...
%PY% build.py
if errorlevel 1 (
  echo.
  echo 构建失败。把上面的报错发给 Hermes。
  pause
  exit /b 1
)

echo.
echo [2/2] 启动预览服务器...
start "灰点预览服务器" /min %PY% -m http.server 8080 --directory docs
ping -n 3 127.0.0.1 >nul
start "" http://localhost:8080

echo.
echo   浏览器已打开： http://localhost:8080
echo   预览服务器跑在最小化的「灰点预览服务器」窗口里，
echo   看完把那个窗口关掉就停止。
echo.
pause
