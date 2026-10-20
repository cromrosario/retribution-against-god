@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ===== update-all-windows.bat (git + deploy) =====
echo Folder: %CD%
echo.

git rev-parse --is-inside-work-tree >nul 2>&1
if errorlevel 1 goto notrepo

rem --- 1. If Downloads\index.html exists, ask whether to copy it to game\index.html ---
if not exist "%USERPROFILE%\Downloads\index.html" goto skipcopy
echo Found: %USERPROFILE%\Downloads\index.html
set "CP="
set /p CP="Copy it to game\index.html ? (y/n): "
if /i not "!CP!"=="y" goto skipcopy
if not exist "game" mkdir "game"
copy /y "%USERPROFILE%\Downloads\index.html" "game\index.html" >nul
if errorlevel 1 goto copyfail
echo Copied.
:skipcopy
echo.

rem --- 2. Stage all changes ---
git add -A
git diff --cached --quiet
if not errorlevel 1 goto nochange

rem --- 3. Commit (first argument is used as the message if given) ---
set "MSG=%~1"
if defined MSG goto docommit
for /f %%i in ('powershell -nologo -command "Get-Date -Format yyyy-MM-dd_HH:mm"') do set "TS=%%i"
set "MSG=update !TS!"
:docommit
echo Commit message: !MSG!
git commit -m "!MSG!"
if errorlevel 1 goto commitfail
goto dopush

:nochange
echo No new changes to commit.

rem --- 4. Push (works even if upstream is not set). A push failure does not stop the deploy step. ---
:dopush
git push -u origin HEAD
if errorlevel 1 goto pushwarn
echo.
echo [OK] Pushed. GitHub Actions will run the tests.
goto askdeploy

:pushwarn
echo.
echo [WARNING] Push failed. The tests on GitHub will NOT run for this change.
echo           Check "git remote -v" - origin must be your GitHub URL.

rem --- 5. Ask whether to deploy ---
:askdeploy
echo.
set "DP="
set /p DP="Deploy to Cloudflare now? (y/n): "
if /i not "!DP!"=="y" goto done

rem --- 6. Find the deploy folder (the one with wrangler.jsonc) ---
set "DEP=%~dp0.."
if exist "%DEP%\wrangler.jsonc" goto depok
set "DEP=%~dp0..\.."
if exist "%DEP%\wrangler.jsonc" goto depok
set "DEP="
set /p DEP="Path of your retribution-deploy folder (the one with wrangler.jsonc): "
if not exist "%DEP%\wrangler.jsonc" goto nofolder
:depok
echo Deploy folder: %DEP%
if not exist "%DEP%\public" mkdir "%DEP%\public"
copy /y "%~dp0game\index.html" "%DEP%\public\index.html"
if errorlevel 1 goto fail
cd /d "%DEP%"
call npx wrangler deploy
if errorlevel 1 goto fail
echo.
echo ===== [OK] Deployed to Cloudflare =====
goto end

:done
echo.
echo ===== Done (not deployed) =====
goto end

:notrepo
echo [ERROR] This folder is not a git repository.
echo Put this file in the rag-repo folder (the one that contains game and tools).
goto fail

:copyfail
echo [ERROR] Could not copy index.html.
goto fail

:commitfail
echo [ERROR] Commit failed. Check the message above.
goto fail

:nofolder
echo ===== [FAILED] wrangler.jsonc not found in that folder =====
goto end

:fail
echo.
echo ===== [FAILED] See the message above =====

:end
echo.
pause
