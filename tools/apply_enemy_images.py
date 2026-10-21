#!/usr/bin/env python3
"""雑魚33体の画像を埋め込む。戦闘の敵表示(enemyArt)で、主・番人以外の雑魚に名前で画像を当てる。
使い方: python3 tools/apply_enemy_images.py game/index.html [--remove]
 画像は tools/img/enemy/<敵の名前>.webp(crop_enemy_sheet.py で元画像から切り出したもの)。
 BOSSIMG:END の後ろに ENEMYIMG ブロックを足し、enemyArt に1行足す。--remove で元にバイト一致。
 黙示の使者・終末の囁きは絵が2種ある。使うのは名前のままのファイル(紫・桃色)。青い方(名前_青)を使うなら、ファイル名を入れ替える。"""
import sys, os, base64
path = sys.argv[1]; remove = "--remove" in sys.argv
here = os.path.dirname(os.path.abspath(__file__))
s = open(path, encoding="utf-8", newline="").read()
B, E = "/* ==== ENEMYIMG:BEGIN", "/* ==== ENEMYIMG:END ==== */\n"
LB, LE = "    /* ENEMYIMG:LINE */", "/* ENEMYIMG:LINE-END */\n"
def strip(s):
    for b, e in ((B, E), (LB, LE)):
        i = s.find(b)
        if i >= 0:
            j = s.index(e, i) + len(e); s = s[:i] + s[j:]
    return s
s = strip(s)
if remove:
    open(path, "w", encoding="utf-8", newline="").write(s); print("removed"); sys.exit()
NAMES = ("邪神兵 動く屍兵 黒い猟犬 顔のない司祭 毒刃の背教者 堕ちた聖騎士 異端の魔導師 屍の群れ 毒を曳く使い魔 鎖の拷問吏 "
         "教団の処刑人 黒翼の眷属 名状しがたい肉塊 星の落とし子 虚ろな賢者 邪神の近衛兵 異形の騎兵 黒き魔導兵 邪神の処刑人 目玉の群れ "
         "神の抜け殻 脈動する肉壁 嗤う聖歌 深淵の信徒 鱗の戦士 深海の影 黄金の亡者 巨獣の眷属 堕天の騎士 快楽に溺れた者 "
         "黙示の使者 地獄の番犬 終末の囁き").split()
rows = []
for n in NAMES:
    p = os.path.join(here, "img", "enemy", n + ".webp")
    assert os.path.exists(p), "画像が無い: " + p
    rows.append('  "%s": "data:image/webp;base64,%s"' % (n, base64.b64encode(open(p, "rb").read()).decode()))
BLOCK = (B + " (自動生成。apply_enemy_images.py で作り直す) ==== */\n"
         "const ENEMYIMG = {\n" + ",\n".join(rows) + "\n};\n" + E)
LINE = (LB + ' if (!(e.boss || e.mini) && typeof ENEMYIMG !== "undefined" && ENEMYIMG[e.key]) return \'<img class="boss-art" alt="" style="object-fit:cover" src="\' + ENEMYIMG[e.key] + \'">\'; ' + LE)
a1 = "/* ==== BOSSIMG:END ==== */\n"
a2 = '    if (e.ghost) return playerImg("ghost");\n'
assert s.count(a1) == 1 and s.count(a2) == 1, "接続箇所の件数が想定と違う"
s = s.replace(a1, a1 + BLOCK).replace(a2, a2 + LINE)
open(path, "w", encoding="utf-8", newline="").write(s); print("applied", len(NAMES), "体")
