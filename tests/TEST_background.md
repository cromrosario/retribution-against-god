# テスト指示 — 経歴システム(apply_background.py)

テストは Git(GitHub Actions / 手元の Playwright)で行う。Claude 環境ではゲームを実行しない。

## 1. 適用
```
python3 tools/apply_background.py game/index.html
```
- 期待: `OK: 経歴システムを適用した`(2回目は「(差し替え)」)。`NG:` が出たら書き換えずに止まっている。
- 外す: `--remove`(適用前とバイト一致に戻る)。

## 2. 静的チェック(smoke_extra.py に足す想定)
| 確認 | 期待 |
|---|---|
| `BG:BEGIN` / `BG:END` の組 | 各1件 |
| `bg: pickBg()` | 1件(`newRun` の G 初期化内) |
| `v += bgB(k);` | 1件(`E()` 内) |
| `bgStatus(b);` | 1件(`trpgStatus(b);` の直前) |
| `bgLog();` | 1件(`startRun` 内) |
| `<script>` 全体を `node --check` | エラーなし |

## 3. 内部値チェック(`?test=1` の `window.__RAG`)
旅立つ直後に実行する。
```js
const g = window.__RAG.G;
// 1) 経歴が付いている
['knight','scholar','thief','priest','survivor'].includes(g.bg)   // true
// 2) 元騎士(knight)のとき、E("hp") が装備なしで 4 以上
//    (複数回リトライして knight を引くか、g.bg = "knight" に書き換えて確認)
window.__RAG.E("hp")
```
- 期待: `g.bg` が5種のどれか。
- 期待: `g.bg` を書き換えて `E()` を呼ぶと、経歴の値だけ変わる(knight: hp 4 / scholar: sp 3・xp 1 / thief: gold 2 / priest: sp 2・herb 1 / survivor: hp 2・herb 1)。
- 乱数の偏り確認: 旅立ちを50回繰り返し、5種すべてが1回以上出る。

## 4. 画面チェック
1. 旅立つ直後のログに「経歴: 元〇〇。…(最大HP+400 など)」が1行出る。
2. ステータス画面に「経歴」の見出しがあり、名前と説明と効果が出る(「契約」の直前)。
3. 途中セーブから再開しても、ステータス画面の経歴が同じ(`G.bg` が保存・復元される)。
4. 旧セーブ(経歴なしの保存)から再開すると「なし。」と出て、エラーにならない。
5. 別ランを始めると、経歴が引き直される(同じとは限らない)。

## 5. 既存への影響(回帰)
- `smoke.py` / `smoke_extra.py` が従来どおり通過する。
- HP の100倍表記が崩れていない(経歴の hp は `recalc` 内で `sc()` される)。
- JS エラーなし。
- 既知: `deriveSet()`(装備比較の表示)は経歴・契約のボーナスを反映しない。
