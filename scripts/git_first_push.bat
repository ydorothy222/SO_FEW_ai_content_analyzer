@echo off
REM 首次提交到新仓库 ydorothy222/SO_FEW_ai_content_analyzer
REM 在项目根目录执行: scripts\git_first_push.bat

cd /d "%~dp0.."

if not exist .git (
  echo [1] 初始化仓库
  git init
)

echo [2] 添加所有文件（.env 和 *.db 已被 .gitignore 排除）
git add .

echo [3] 提交
git commit -m "feat: AI 内容永动机 ToC + 用户用量控制 + Python 3.8 兼容"

echo [4] 主分支 main
git branch -M main

echo [5] 添加远程（若已存在会报错，可先 git remote remove origin）
git remote add origin https://github.com/ydorothy222/SO_FEW_ai_content_analyzer.git 2>nul
if errorlevel 1 (
  echo 远程已存在，改为设置 URL...
  git remote set-url origin https://github.com/ydorothy222/SO_FEW_ai_content_analyzer.git
)

echo [6] 推送到 GitHub
git push -u origin main

pause
