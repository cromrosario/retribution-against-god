@echo off
cd /d "%~dp0"
set DEP=%~dp0..\..
if not exist "%DEP%\wrangler.jsonc" set /p DEP=Path of your retribution-deploy folder (the one with wrangler.jsonc): 
if not exist "%DEP%\wrangler.jsonc" goto nofolder
copy /y "%~dp0game\index.html" "%DEP%\public\index.html"
if errorlevel 1 goto fail
cd /d "%DEP%"
call npx wrangler deploy
if errorlevel 1 goto fail
echo.
echo ===== [OK] Deployed to Cloudflare =====
goto end
:nofolder
echo ===== [FAILED] wrangler.jsonc not found in that folder =====
goto end
:fail
echo.
echo ===== [FAILED] See the message above =====
:end
pause
