@echo off
chcp 65001 >nul
cd /d "%~dp0"
git add -A
git commit -m "update" || echo (変更がないか、すでにコミット済みです)
git push
if errorlevel 1 (
  echo.
  echo ===== [失敗] pushできませんでした。上のメッセージを確認してください =====
  pause
  exit /b 1
)
echo.
echo ===== [OK] GitHubへ更新しました。テストの結果を待っています... =====
timeout /t 6 >nul
for /f %%i in ('gh run list --limit 1 --json databaseId -q ".[0].databaseId"') do set RID=%%i
gh run watch %RID% --exit-status >nul
if errorlevel 1 (
  echo.
  echo ===== [テスト失敗] 下のエラーを私(Claude)に貼ってください =====
  gh run view %RID% --log-failed
) else (
  echo.
  echo ===== [テスト成功] 問題なし =====
)
pause
