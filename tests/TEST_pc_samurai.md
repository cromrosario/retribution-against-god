# TEST_pc_samurai — 侍の自キャラ画像

対象: `tools/apply_pc_samurai.py`(`PC-JS` / `PC-CSS` と、`PC:LINE` 1行・`PC:INLINE` 2か所)。テストは Git 側で行う。

## 静的チェック
1. `PC-JS:BEGIN/END`・`PC-CSS:BEGIN/END` が各1件。`PC:LINE */` が1件(`render()` の先頭)。`PC:INLINE */` が3件(`playerImg`・`statusPortrait`・タイトルのステージの `key = "title:" + currentJob().id`)。
2. `const PC_SPRITE` に `samurai` があり、値が `data:image/png;base64,` で始まる。
3. `PLAYER_SRC`(従来のドット絵)が残っている(他の職業用)。

## 内部値チェック(`?test=1` の `window.__RAG`)
1. 侍で旅立つと、`#pcImg` の `src` が `PC_SPRITE.samurai` と一致し、`classList` に `wide` がある。侍以外の職業では `PLAYER_SRC` のまま・`wide` なし。
2. ステータス画面の先頭の肖像(`.pc-big img`)が、侍のときは `wide`(幅 128px)。
3. タイトル画面で「職業を選ぶ」から侍を選んだ直後、ステージの自キャラ(`#sigil img`)の `src` が侍の絵になる。別の職業に選び直すと、従来の絵に戻る(以前は、最初に表示した絵のまま作り直されなかった)。
4. 亡霊(`playerImg("ghost")`)が、侍のときは侍の絵(モノクロ・左右反転)になる。

## 実機確認
- 戦闘のHUD(自キャラ 64px)で、侍の絵が小さすぎないか・見やすいか。
- ステータス画面・タイトルでの大きさ(128px。横長で、刀が左に伸びている)。
- 背景が透明で、枠の背景(青のグラデーション)と合っているか。
