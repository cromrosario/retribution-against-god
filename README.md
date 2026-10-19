# Retribution Against God
- `game/index.html` … ゲーム本体(単一HTML)
- `tests/smoke.py` … 自動テスト(pushでGitHub Actionsが実行)
## 使い方
- 初回: Windowsは `setup-windows.bat`、Macは `setup-mac.command` をダブルクリック
- 更新後: `update-windows.bat` / `update-mac.command` をダブルクリック(pushしてテストが走る)
## 結果表示
update スクリプトは、push成功 [OK]/失敗、続けてテスト 成功/失敗 を画面に表示します。
## 公開URL
pushしてテストが通ると、GitHub Pagesに自動公開される。
初回のみ GitHub の Settings → Pages → Source を「GitHub Actions」にする。
URL: https://<GitHubユーザー名>.github.io/retribution-against-god/
