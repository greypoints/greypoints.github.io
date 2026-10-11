@echo off
cd /d "%~dp0"

rem 让 Python 用 GBK 输出，否则中文提示在 cmd 窗口里会乱码
set PYTHONIOENCODING=gbk

rem 选择可用的 Python（优先官方 launcher，其次 PATH 里的 python）
set "PY=py -3"
%PY% -c "import markdown" >nul 2>&1
if errorlevel 1 set "PY=python"

echo ================================================
echo   更新网站（构建 + 上传到 GitHub）
echo ================================================
echo.

git remote get-url origin >nul 2>&1
if errorlevel 1 (
  echo 还没有连接远程仓库。
  echo 请先双击运行一次「首次部署.bat」。
  pause
  exit /b 1
)

echo [1/3] 构建网站...
%PY% build.py
if errorlevel 1 (
  echo.
  echo 构建失败，已中止。把上面的报错发给 Hermes。
  pause
  exit /b 1
)

echo.
echo [2/3] 记录改动...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "update site content"
) else (
  echo   没有内容变化，跳过提交。
)

echo.
echo [3/3] 上传到 GitHub...
git push
if errorlevel 1 (
  echo.
  echo 上传失败：检查网络后重试。
  pause
  exit /b 1
)

echo.
echo ================================================
echo   完成！约 1 分钟后生效：
echo   https://greypoints.github.io
echo ================================================
pause
