#!/bin/sh
cd "$(dirname "$0")"
command -v brew >/dev/null || /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
command -v git >/dev/null || brew install git
command -v gh >/dev/null || brew install gh
gh auth status >/dev/null 2>&1 || gh auth login --web
git init -b main 2>/dev/null
git add -A && git commit -m "init"
gh repo create retribution-against-god --private --source=. --push
echo "完了。GitHubのActionsタブで結果を確認できます"
