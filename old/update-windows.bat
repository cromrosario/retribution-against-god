@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
cd /d "%~dp0"

echo ===== update-windows.bat =====
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
echo No new changes to commit. Trying to push existing commits...

rem --- 4. Push (works even if upstream is not set) ---
:dopush
git push -u origin HEAD
if errorlevel 1 goto pushfail
echo.
echo ===== [OK] Pushed. Check GitHub Actions for the test result. =====
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

:pushfail
echo.
echo ===== [FAILED] Could not push. Check the message above =====
goto fail

:fail
echo.
pause
exit /b 1

:end
echo.
pause
exit /b 0
