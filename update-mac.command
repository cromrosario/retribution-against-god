#!/bin/sh
cd "$(dirname "$0")"
git add -A
git commit -m "update" || echo "(変更がないか、すでにコミット済みです)"
if ! git push; then
  echo "===== [失敗] pushできませんでした。上のメッセージを確認してください ====="
  exit 1
fi
echo "===== [OK] GitHubへ更新しました。テストの結果を待っています... ====="
sleep 6
RID=$(gh run list --limit 1 --json databaseId -q ".[0].databaseId")
if gh run watch "$RID" --exit-status >/dev/null; then
  echo "===== [テスト成功] 問題なし ====="
else
  echo "===== [テスト失敗] 下のエラーを私(Claude)に貼ってください ====="
  gh run view "$RID" --log-failed
fi
