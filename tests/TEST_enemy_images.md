# TEST_enemy_images — 雑魚33体の画像

対象: `tools/apply_enemy_images.py`(`ENEMYIMG` ブロックと、`enemyArt` 内の `ENEMYIMG:LINE` 1行)。テストは Git 側で行う。

## 静的チェック
1. `ENEMYIMG:BEGIN`/`ENEMYIMG:END` が各1件、`ENEMYIMG:LINE` が1件(`enemyArt` 内、`e.ghost` の行の直後)。
2. `ENEMYIMG` のキーが33個で、すべて `ENEMIES` と `Object.assign(ENEMY_ARCH …)` の敵名と一致する(名前の取りこぼしなし)。
3. 各値が `data:image/webp;base64,` で始まる。

## 内部値チェック(`?test=1` の `window.__RAG`)
1. `makeEnemy()` で作った雑魚(`boss`・`mini` でない、`key` が `ENEMYIMG` にある)の戦闘開始直後、`#sigil img` が存在し、`src` が `data:image/webp` で始まる。
2. 主・番人(`boss` / `mini`)は従来どおり `BOSSIMG` の画像のまま。
3. 拠点ごとの雑魚(`ZONES[z].minions`、`ENEMYIMG` に無い名前)は従来のドット絵(`#sigil svg`)のまま。
4. 強敵(`【強敵】` 付き)でも同じ画像が出る(`key` は付かない素の名前)。
5. JS エラーが出ない。

## 実機確認
- 序盤〜深層の各雑魚で、敵の枠に画像が正しく出ているか(名前と絵が合っているか)。
- 枠(正方形)に合わせて左右がトリミングされる(`object-fit: cover`)。顔や武器が切れすぎていないか。
- 黙示の使者・終末の囁きは、紫・桃色の絵を使っている。青い方に替えたいときは `tools/img/enemy/` のファイル名を入れ替えて `apply_enemy_images.py` を再実行する。
