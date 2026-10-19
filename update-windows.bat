@echo off
cd /d "%~dp0"
git add -A
git commit -m "update"
git push
if errorlevel 1 goto pushfail
echo.
echo ===== [OK] Pushed to GitHub. Waiting for test result... =====
timeout /t 8 /nobreak >nul
for /f %%i in ('gh run list --limit 1 --json databaseId -q ".[0].databaseId"') do set RID=%%i
gh run watch %RID% --exit-status >nul
if errorlevel 1 goto testfail
echo.
echo ===== [TEST PASSED] Everything is OK =====
goto end
:testfail
echo.
echo ===== [TEST FAILED] Paste the error below to Claude =====
gh run view %RID% --log-failed
goto end
:pushfail
echo.
echo ===== [FAILED] Could not push. Check the message above =====
:end
pause
