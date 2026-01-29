@echo off
REM 本地测试后，提交并推送到 GitHub（请先确认 .env 未被 add）
REM 在项目根目录执行: scripts\git_push.bat

cd /d "%~dp0.."

echo [1] 检查 .gitignore 是否排除 .env ...
findstr /C:".env" .gitignore >nul 2>&1
if errorlevel 1 (
  echo 警告: .gitignore 中未找到 .env，请确认不会提交密钥
  pause
) else (
  echo .env 已在 .gitignore 中
)

echo.
echo [2] git status
git status

echo.
echo [3] 添加所有文件（.env 和 *.db 会被忽略）
git add .

echo.
echo [4] 提交
git commit -m "feat: AI 内容永动机 ToC + 用户用量控制 + 邮件欢迎"

echo.
echo [5] 若尚未添加远程，请先执行:
echo     git remote add origin https://github.com/dorothy21312/SO_FEW_ai_content_analyzer.git
echo     git branch -M main
echo.
echo [6] 推送
git push -u origin main

pause
