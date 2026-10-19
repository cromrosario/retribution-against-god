#!/bin/sh
# 初回のみ実行: GitHubリポジトリを作成してpush → 以後はpushのたびに自動テスト
# 事前に `gh auth login` を済ませておく
set -e
git init -b main 2>/dev/null || true
git add -A && git commit -m "init" || true
gh repo create retribution-against-god --private --source=. --push
echo "pushしました。GitHubのActionsタブで結果を確認できます"
