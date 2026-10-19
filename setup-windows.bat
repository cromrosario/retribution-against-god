@echo off
cd /d "%~dp0"
echo === First-time setup ===
where git >nul 2>nul
if errorlevel 1 winget install --id Git.Git -e --silent
where gh >nul 2>nul
if errorlevel 1 winget install --id GitHub.cli -e --silent
echo If you just installed Git or GitHub CLI, close this window and run this file again.
gh auth status >nul 2>nul
if errorlevel 1 gh auth login --web
git init -b main
git add -A
git commit -m "init"
gh repo create retribution-against-god --private --source=. --push
if errorlevel 1 goto fail
echo.
echo ===== [OK] Done. Open the Actions tab of the repository on GitHub =====
goto end
:fail
echo.
echo ===== [FAILED] See the message above =====
:end
pause
