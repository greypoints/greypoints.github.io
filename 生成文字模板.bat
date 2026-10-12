@echo off
cd /d "%~dp0"

rem 让 Python 用 GBK 输出，否则中文提示在 cmd 窗口里会乱码
set PYTHONIOENCODING=gbk

rem 选择可用的 Python（优先官方 launcher，其次 PATH 里的 python）
set "PY=py -3"
%PY% -c "import markdown" >nul 2>&1
if errorlevel 1 set "PY=python"

echo ================================================
echo   生成/重建 网站文字.txt
echo ================================================
echo.
echo   注意：会覆盖 网站文字.txt 里已有的修改。
echo   用途：想把文字改回默认值，或文件被改坏了要重建。
echo.

%PY% gentext.py
if errorlevel 1 (
  echo.
  echo 生成失败，已中止。把上面的报错发给 Hermes。
  pause
  exit /b 1
)

echo.
echo ================================================
echo   完成。现在可以打开 网站文字.txt 改文字了。
echo   改完双击「更新网站.bat」上线。
echo ================================================
pause
