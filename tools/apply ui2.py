#!/usr/bin/env python3
"""UI調整その2: (1) 戦闘外はHP/MPを画面の一番下へ (2) イベント画面の選択肢をさらに小さく (3) イベント挿絵をさらに大きく。
使い方: python3 tools/apply_ui2.py game/index.html [--remove]  ※ BGFIX-CSS の後ろに UI2-CSS を足す"""
import sys
path = sys.argv[1]; remove = "--remove" in sys.argv
s = open(path, encoding="utf-8", newline="").read()
B, E = "/* ==== UI2-CSS:BEGIN", "/* ==== UI2-CSS:END ==== */\n"
i = s.find(B)
if i >= 0:
    j = s.index(E, i) + len(E); s = s[:i] + s[j:]
if remove:
    open(path, "w", encoding="utf-8", newline="").write(s); print("removed"); sys.exit()
CSS = B + " (自動挿入。apply_ui2.py を直して再実行する) ==== */\n" + r"""/* 1. 戦闘外: HP/MP(.me)を画面の一番下へ(.app は縦並びの flex。order で最後に回す)。戦闘中は今までの位置 */
body:not(.fighting) .me { order: 99; }
/* 2. 選択肢をさらに小さく(戦闘外・タイトル以外)。数値は下の1行を変えれば調整できる */
body:not(.fighting):not(.home) .choices:not(.battle) { padding: 2px; }
body:not(.fighting):not(.home) .choices:not(.battle) button { min-height: 28px; padding: 2px 8px 2px 28px; column-gap: 6px; font-size: 13px; line-height: 1.25; }
body:not(.fighting):not(.home) .choices:not(.battle) .ic { width: 14px; height: 14px; }
body:not(.fighting):not(.home) .choices:not(.battle) .sub-note { font-size: 10px; line-height: 1.2; }
/* 3. イベント挿絵をさらに大きく: 挿絵があるときだけログ枠を画面の左右いっぱいまで広げ、比率を 4:3(横長を少し縦にトリミング)、高さは 42vh まで */
body:not(.fighting):not(.home) .log:has(img.ev-art:not(.boss-intro)) { margin-left: -10px; margin-right: -10px; border-left: 0; border-right: 0; border-radius: 0; }
body .log img.ev-art:not(.boss-intro) { aspect-ratio: 4 / 3 !important; max-height: 42vh !important; }
""" + E
a = "/* ==== BGFIX-CSS:END ==== */\n"
assert s.count(a) == 1, "接続箇所の件数が想定と違う(先に apply_bgfix.py を適用)"
s = s.replace(a, a + CSS)
open(path, "w", encoding="utf-8", newline="").write(s); print("applied")
