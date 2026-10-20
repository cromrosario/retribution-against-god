#!/usr/bin/env python3
"""画面上部の2行(#statsLine=職業・能力値 / #gearLine=装備・スキル・アビリティ・職業パッシブ数)を常時非表示にする。

  python3 apply_hide_lines.py ../game/index.html           # 非表示にする(再実行可)
  python3 apply_hide_lines.py ../game/index.html --remove  # 元に戻す

CSS を1行変えるだけ。要素と描画コードは残す(テストが要素を参照しても壊れない)。
同じ情報はステータス画面・持ち物画面で見られる。
"""
import sys, io
OLD = "body.fighting .stats, body.fighting .gear { display: none !important; }"
NEW = ".stats, .gear, body.fighting .stats, body.fighting .gear { display: none !important; } /* HIDE_LINES */"

def main():
    if len(sys.argv) < 2: print("NG: 使い方: apply_hide_lines.py <index.html> [--remove]"); sys.exit(1)
    path, remove = sys.argv[1], "--remove" in sys.argv
    t = io.open(path, encoding="utf-8").read()
    # NEW は OLD を部分文字列として含むので、必ず NEW の有無を先に判定する
    if remove:
        if t.count(NEW) != 1: print("NG: 非表示の記述が1件でない(%d件)。書き換えない" % t.count(NEW)); sys.exit(1)
        t = t.replace(NEW, OLD)
    else:
        if t.count(NEW) == 1: print("OK: すでに非表示(変更なし)"); return
        if t.count(NEW) > 1 or t.count(OLD) != 1: print("NG: 対象の CSS が想定外の件数。書き換えない"); sys.exit(1)
        t = t.replace(OLD, NEW)
    io.open(path, "w", encoding="utf-8").write(t)
    print("OK: 元に戻した" if remove else "OK: 2行を非表示にした")

if __name__ == "__main__": main()
