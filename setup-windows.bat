@echo off
cd /d "%~dp0"
echo === First-time setup (no GitHub CLI needed) ===
echo.
echo 1) In your browser, open https://github.com/new
echo 2) Repository name: retribution-against-god  (Private is OK)
echo 3) Do NOT add README/.gitignore. Click "Create repository"
echo 4) Copy the repository URL (like https://github.com/YOURNAME/retribution-against-god.git)
echo.
set /p URL=Paste the URL here and press Enter: 
git init -b main
git add -A
git commit -m "init"
git remote remove origin >nul 2>nul
git remote add origin %URL%
git push -u origin main
if errorlevel 1 goto fail
echo.
echo ===== [OK] Done. Open the repository page on GitHub and click the Actions tab =====
goto end
:fail
echo.
echo ===== [FAILED] See the message above. A browser login window may have appeared - approve it and run this file again =====
:end
pause
