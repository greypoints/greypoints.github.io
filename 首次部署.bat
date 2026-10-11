@echo off
cd /d "%~dp0"

rem 让 Python 用 GBK 输出，否则中文提示在 cmd 窗口里会乱码
set PYTHONIOENCODING=gbk

rem 选择可用的 Python（优先官方 launcher，其次 PATH 里的 python）
set "PY=py -3"
%PY% -c "import markdown" >nul 2>&1
if errorlevel 1 set "PY=python"

echo ================================================
echo   首次部署（只做一次，之后用「更新网站.bat」）
echo ================================================
echo.
echo 开始前请确认你已经：
echo   1. 有 GitHub 账号
echo   2. 创建了名为  greypoints.github.io  的空仓库
echo      创建地址 https://github.com/new
echo      可见性必须选 Public（免费账户只有公开仓库能用 Pages）
echo      不要勾选 README / .gitignore / license，保持空白
echo.
pause

echo [1/5] 构建网站...
%PY% build.py
if errorlevel 1 (
  echo 构建失败，已中止。
  pause
  exit /b 1
)

echo.
echo [2/5] 初始化本地仓库...
if not exist ".git" git init
git branch -M main

echo.
echo [3/5] 记录文件...
git add -A
git diff --cached --quiet
if errorlevel 1 (
  git commit -m "first commit"
) else (
  echo   没有需要提交的改动。
)

echo.
echo [4/5] 连接远程仓库...
git remote remove origin >nul 2>&1
git remote add origin https://github.com/greypoints/greypoints.github.io.git
git remote -v

echo.
echo [5/5] 上传...
echo.
echo   >>> 会弹出登录窗口，选 "Sign in with your browser" <<<
echo   >>> 用 GitHub 账号登录，授权一次以后不用再登 <<<
echo.
git push -u origin main
if errorlevel 1 (
  echo.
  echo 上传失败。常见原因：
  echo   1. 仓库名不是 greypoints.github.io
  echo   2. 仓库里已经有文件（删掉重建一个空的）
  echo   3. 网络问题，重试一次
  pause
  exit /b 1
)

echo.
echo ================================================
echo   上传成功！最后一步（只做一次）：
echo.
echo   打开 https://github.com/greypoints/greypoints.github.io/settings/pages
echo   Source 选 "Deploy from a branch"
echo   Branch 选 main ，文件夹选 /docs ，点 Save
echo.
echo   等 1-2 分钟后访问： https://greypoints.github.io
echo ================================================
pause
