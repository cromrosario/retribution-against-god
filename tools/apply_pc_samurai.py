#!/usr/bin/env python3
"""侍を選んだときの自キャラの絵を、専用のドット絵に変える(戦闘のHUD・ステータス画面・タイトル・亡霊)。
 絵は tools/img/pc/samurai.png(128x130、背景は透明。元の大きな画像から crop_pc_sprite.py で作成)。
 タイトル画面では、職業を選び直したときに絵が作り直されるよう、ステージのキャッシュのキーに職業idを足す。
 他の職業は、今までのドット絵のまま。職業を増やすときは tools/img/pc/<職業id>.png を足し、下の PC_JOBS に職業idを足す。
使い方: python3 tools/apply_pc_samurai.py game/index.html [--remove]
 FIT-JS の後ろに PC-JS、UI3-CSS の後ろに PC-CSS を足し、元のコード4か所に挿入・書き換えする。--remove で元にバイト一致。"""
import sys, os, base64
path = sys.argv[1]; remove = "--remove" in sys.argv
here = os.path.dirname(os.path.abspath(__file__))
PC_JOBS = ["samurai"]
s = open(path, encoding="utf-8", newline="").read()
CB, CE = "/* ==== PC-CSS:BEGIN", "/* ==== PC-CSS:END ==== */\n"
JB, JE = "/* ==== PC-JS:BEGIN", "/* ==== PC-JS:END ==== */\n"
LB, LE = "/* PC:LINE */", "/* PC:LINE-END */\n"
PAIRS = [
 ('    else { key = "title"; seed = "邪神"; strong = true; name = "Retribution Against God"; sub = ""; roman = true; artSvg = playerImg("big"); }\n',
  '    else { key = "title:" + currentJob().id; seed = "邪神"; strong = true; name = "Retribution Against God"; sub = ""; roman = true; artSvg = playerImg("big"); } /* PC:INLINE */\n'),
 ("  const playerImg = (cls) => '<img class=\"pc ' + (cls || \"\") + '\" alt=\"\" src=\"' + PLAYER_SRC + '\">';\n",
  "  const playerImg = (cls) => '<img class=\"pc ' + (cls || \"\") + '\" alt=\"\" src=\"' + (typeof pcSrc === \"function\" ? pcSrc() : PLAYER_SRC) + '\">'; /* PC:INLINE */\n"),
 ("  if (pc && pc.src) { const im = document.createElement(\"img\"); im.src = pc.src; im.alt = \"\"; w.appendChild(im); }\n",
  "  if (pc && pc.src) { const im = document.createElement(\"img\"); im.src = pc.src; im.alt = \"\"; if (pc.classList.contains(\"wide\")) im.className = \"wide\"; w.appendChild(im); } /* PC:INLINE */\n"),
]
RENDER = "  function render() {\n    if (!G) return;\n    recalc();\n"
RENDER_N = RENDER + "    " + LB + " if (typeof syncPcImg === \"function\") syncPcImg(); " + LE
def strip(s):
    for b, e in ((CB, CE), (JB, JE)):
        i = s.find(b)
        if i >= 0:
            j = s.index(e, i) + len(e); s = s[:i] + s[j:]
    s = s.replace(RENDER_N, RENDER)
    for old, new in PAIRS:
        s = s.replace(new, old)
    return s
s = strip(s)
if remove:
    open(path, "w", encoding="utf-8", newline="").write(s); print("removed"); sys.exit()
rows = []
for j in PC_JOBS:
    p = os.path.join(here, "img", "pc", j + ".png")
    assert os.path.exists(p), "画像が無い: " + p
    rows.append('  %s: "data:image/png;base64,%s"' % (j, base64.b64encode(open(p, "rb").read()).decode()))
CSS = CB + " (自動挿入。apply_pc_samurai.py を直して再実行する) ==== */\n" + r"""/* 職業専用の絵(横長の全身像): 戦闘のHUDは少し大きく、ステータス画面は等倍(128px) */
body.fighting .me > .pc.wide { width: 64px; }
.pc-big img.wide { width: 128px; padding: 2px; }
""" + CE
JS = JB + " (自動挿入。apply_pc_samurai.py を直して再実行する) ==== */\n" + \
 "/* 職業ごとの自キャラの絵。ここに無い職業は、従来の PLAYER_SRC */\nconst PC_SPRITE = {\n" + ",\n".join(rows) + "\n};\n" + r"""function pcSrc() {
  const j = (G && G.job) || (typeof currentJob === "function" ? currentJob() : null);
  return (j && PC_SPRITE[j.id]) || PLAYER_SRC;
}
/* HUD の自キャラ(#pcImg)を、いまの職業の絵に合わせる。render() の先頭から呼ばれる */
function syncPcImg() {
  const pc = document.getElementById("pcImg"); if (!pc || !G) return;
  const key = G.job.id;
  if (pc.dataset.k === key) return;
  pc.dataset.k = key; pc.src = pcSrc();
  pc.classList.toggle("wide", !!PC_SPRITE[key]);
}
""" + JE
a1 = "/* ==== UI3-CSS:END ==== */\n"; a2 = "/* ==== FIT-JS:END ==== */\n"
assert s.count(a1) == 1 and s.count(a2) == 1, "UI3-CSS / FIT-JS が見つからない(先に適用)"
assert s.count(RENDER) == 1, "render の接続箇所が想定と違う"
for old, new in PAIRS: assert s.count(old) == 1, "接続箇所の件数が想定と違う: " + old[:50]
s = s.replace(RENDER, RENDER_N)
for old, new in PAIRS: s = s.replace(old, new)
s = s.replace(a1, a1 + CSS).replace(a2, a2 + JS)
open(path, "w", encoding="utf-8", newline="").write(s); print("applied", PC_JOBS)
