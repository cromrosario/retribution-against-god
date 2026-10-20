#!/usr/bin/env python3
"""経歴システム(ランダムで「元〇〇」を1つ付与)を game/index.html に適用する。

使い方:
  python3 apply_background.py ../game/index.html           # 適用(2回目以降は差し替え)
  python3 apply_background.py ../game/index.html --remove  # 外す

内容:
  - ラン開始時に5種からランダムで1つ決め、G.bg(id文字列)に保存 → 途中セーブに自動で載る
  - 効果は E() に加算(契約と同じ経路)。ステータス画面に「経歴」を表示
  - 想定外の件数のときは書き換えずに止まる
"""
import sys, re, io

BEGIN = "/* ==== BG:BEGIN (自動挿入ブロック。編集は apply_background.py の BLOCK で行い、再実行する) ==== */"
END = "/* ==== BG:END ==== */"

BLOCK = BEGIN + r'''
/* ---------- 経歴: ラン開始時にランダムで1つ。効果は小さな初期ボーナスのみ ---------- */
const BGS = [
  { id: "knight",  n: "元騎士",         b: { hp: 4 },           t: "守るために剣を取っていた。体が頑丈だ。" },
  { id: "scholar", n: "元学者",         b: { sp: 3, xp: 1 },    t: "書物で世界を学んだ。覚えが早い。" },
  { id: "thief",   n: "元盗賊",         b: { gold: 2 },         t: "拾えるものは拾う。手癖が悪い。" },
  { id: "priest",  n: "元聖職者",       b: { sp: 2, herb: 1 },  t: "祈りと手当ての心得がある。" },
  { id: "survivor", n: "王国の生存者",  b: { hp: 2, herb: 1 }, t: "滅びた国から逃げ延びた。しぶとい。" }
];
const bgOf = () => (G && G.bg ? BGS.find((x) => x.id === G.bg) || null : null);
function pickBg() { return BGS[Math.floor(Math.random() * BGS.length)].id; }
function bgB(k) { const o = bgOf(); return (o && o.b && o.b[k]) || 0; }
function bgLog() { const o = bgOf(); if (o) log("経歴: " + o.n + "。" + o.t + "(" + bText(o.b) + ")"); }
function bgStatus(b) {
  const o = bgOf();
  b.appendChild(mkEl("h4", "", "経歴"));
  if (!o) { b.appendChild(mkEl("p", "dim", "なし。")); return; }
  const box = mkEl("div", "item");
  box.appendChild(mkEl("div", "iname", o.n));
  box.appendChild(mkEl("div", "idesc", o.t + "　" + bText(o.b)));
  b.appendChild(box);
}
''' + END + "\n"

# (旧文字列, 新文字列, 期待件数) ※適用後の文字列で適用済みを判定
PATCHES = [
    ("zc: 0, zord: [], sv: 2\n", "zc: 0, zord: [], sv: 2, bg: pickBg()\n", "zc: 0, zord: [], sv: 2, bg: pickBg()"),
    ("      v += pactB(k);\n", "      v += pactB(k);\n      v += bgB(k);\n", "      v += bgB(k);"),
    ("      trpgStatus(b);\n", "      bgStatus(b);\n      trpgStatus(b);\n", "      bgStatus(b);"),
    ('    log("仲間の形見を背負い、最初の拠点へ向かう。");\n',
     '    log("仲間の形見を背負い、最初の拠点へ向かう。");\n    bgLog();\n', "    bgLog();"),
]
ANCHOR = "/* ==== TRPG:BEGIN"

def die(msg):
    print("NG:", msg); sys.exit(1)

def strip_block(t):
    s = t.find(BEGIN)
    if s < 0: return t, False
    e = t.find(END, s)
    if e < 0: die("BG:END が見つからない")
    return t[:s] + t[e + len(END) + 1:], True

def main():
    if len(sys.argv) < 2: die("使い方: apply_background.py <index.html> [--remove]")
    path, remove = sys.argv[1], "--remove" in sys.argv
    t = io.open(path, encoding="utf-8").read()
    t, had = strip_block(t)
    # 一旦すべて元に戻す
    for old, new, mark in PATCHES:
        if t.count(new) == 1: t = t.replace(new, old)
        elif t.count(mark) > 1: die("適用済み箇所が複数ある: " + mark)
    if remove:
        for old, new, mark in PATCHES:
            if t.count(old) != 1: die("元の接続箇所が1件でない: " + repr(old[:40]))
        io.open(path, "w", encoding="utf-8").write(t)
        print("OK: 経歴システムを外した"); return
    for old, new, mark in PATCHES:
        if t.count(old) != 1: die("接続箇所が1件でない(%d件): %r" % (t.count(old), old[:40]))
    if t.count(ANCHOR) != 1: die("TRPG:BEGIN が1件でない")
    for old, new, mark in PATCHES: t = t.replace(old, new)
    t = t.replace(ANCHOR, BLOCK + ANCHOR)
    io.open(path, "w", encoding="utf-8").write(t)
    print("OK: 経歴システムを適用した(差し替え)" if had else "OK: 経歴システムを適用した")

if __name__ == "__main__": main()
