#!/usr/bin/env python3
"""雑魚一覧の画像(1024x1536、名前ラベル入り)から、敵1体ごとの画像を切り出す。
使い方: python3 tools/crop_enemy_sheet.py 元画像.png [出力フォルダ=tools/img/enemy]
ラベル(上の約31px)と枠を除いて webp(高さ最大200px)で保存する。ファイル名は敵の名前。
黙示の使者・終末の囁きは絵が2種ある。ゲームで使うのは USE の指定(紫の黙示の使者・桃色の終末の囁き)。青い方は『名前_青』で保存する。"""
import sys, os
from PIL import Image
src = sys.argv[1]; out = sys.argv[2] if len(sys.argv) > 2 else "tools/img/enemy"
os.makedirs(out, exist_ok=True)
im = Image.open(src).convert("RGB")
XS = [(17, 211), (215, 410), (414, 608), (614, 809), (813, 1007)]
Y = {0: (32, 243), 1: (275, 481), 2: (509, 704), 3: (734, 930), 4: (957, 1151), 5: (1160, 1332), 6: (1337, 1516)}
GRID = [
    ["邪神兵", "動く屍兵", "黒い猟犬", "顔のない司祭", "毒刃の背教者"],
    ["堕ちた聖騎士", "異端の魔導師", "屍の群れ", "毒を曳く使い魔", "鎖の拷問吏"],
    ["教団の処刑人", "黒翼の眷属", "名状しがたい肉塊", "星の落とし子", "虚ろな賢者"],
    ["邪神の近衛兵", "異形の騎兵", "黒き魔導兵", "邪神の処刑人", "目玉の群れ"],
    ["神の抜け殻", "脈動する肉壁", "嗤う聖歌", "深淵の信徒", "鱗の戦士"],
    ["深海の影", "黄金の亡者", "巨獣の眷属", "堕天の騎士", "快楽に溺れた者"],
    ["黙示の使者_青", "地獄の番犬", "終末の囁き_青", "黙示の使者", "終末の囁き"],
]
LABEL = 31; EDGE = 3; MAXH = 200
for r, row in enumerate(GRID):
    for c, name in enumerate(row):
        y0, y1 = Y[r]
        if r == 5 and c >= 3: y0 = 1178          # 深層2 の見出しの下から始まるタイル
        x0, x1 = XS[c]
        t = im.crop((x0 + EDGE, y0 + LABEL, x1 - EDGE, y1 - EDGE))
        if t.height > MAXH: t = t.resize((round(t.width * MAXH / t.height), MAXH), Image.LANCZOS)
        t.save(os.path.join(out, name + ".webp"), "WEBP", quality=82, method=6)
print("done")
