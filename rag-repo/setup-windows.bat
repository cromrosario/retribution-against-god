@echo off
chcp 65001 >nul
echo === 初回セットアップ(Windows) ===
where git >nul 2>nul || winget install --id Git.Git -e --silent
where gh >nul 2>nul || winget install --id GitHub.cli -e --silent
echo ※ 新しく入れた場合は、このウィンドウを閉じてもう一度ダブルクリックしてください
gh auth status >nul 2>nul || gh auth login --web
cd /d "%~dp0"
git init -b main
git add -A
git commit -m "init"
gh repo create retribution-against-god --private --source=. --push
echo.
echo 完了。GitHubのActionsタブでテスト結果が見られます。
pause
