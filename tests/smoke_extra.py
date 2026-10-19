#!/usr/bin/env python3
"""
Retribution Against God 追加スモークテスト(既存の tests/smoke.py とは別ファイル)

実行(手元の Git 側で実行。Claude 上では実行しない):
    pip install playwright && playwright install chromium
    python tests/smoke_extra.py [game/index.html]

ゲーム本体は IIFE で内部状態(G など)を外に出していないため、
ここでは「ソースの静的チェック」と「画面(DOM)の動作チェック」だけを行う。
効果の数値(HP吸収・受け流し等)の検証は、ゲーム側に ?test=1 用の入口を足してから拡張する。
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = [ROOT / "game" / "index.html", ROOT / "index.html"]
HTML = Path(sys.argv[1]) if len(sys.argv) > 1 else next((p for p in CANDIDATES if p.exists()), None)

failures, warnings = [], []


def check(ok, msg):
    print(("  OK   " if ok else "  FAIL ") + msg)
    if not ok:
        failures.append(msg)


def warn(msg):
    print("  WARN " + msg)
    warnings.append(msg)


def static_checks(src):
    print("[静的チェック]")
    # --- 構文 ---
    scripts = re.findall(r"<script[^>]*>(.*?)</script>", src, re.S)
    main = max(scripts, key=len) if scripts else ""
    check(bool(main), "メインの <script> がある")
    node = shutil.which("node")
    if node and main:
        with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False, encoding="utf-8") as f:
            f.write(main)
            tmp = f.name
        r = subprocess.run([node, "--check", tmp], capture_output=True, text=True)
        check(r.returncode == 0, "node --check が通る" + ("" if r.returncode == 0 else ": " + r.stderr[:200]))
        os.unlink(tmp)
    else:
        warn("node が無いので構文チェックを省略")

    # --- HUD ---
    check('id="xpBar"' not in src and 'id="lvLabel"' not in src and 'id="xpNum"' not in src,
          "HUDから経験値バー(xpBar/lvLabel/xpNum)が外れている")
    check("bars2 vital" in src, "HP/MP が .vital で大きく表示される")
    check("body.fighting .stats, body.fighting .gear" in src, "戦闘中に statsLine/gearLine を隠すCSSがある")

    # --- ステータス・器用さ ---
    check('skl: "器用さ"' in src, "器用さ(skl)がステータス定義にある")
    check("const SKL = () =>" in src, "旧セーブ対策の SKL() がある")
    check(re.search(r"Math\.max\(12,", src) is not None, "会心範囲の下限が 12")
    check("const critSyn" in src, "命中が高いほど会心が広がる critSyn がある")

    # --- 装備 手・脚 ---
    check("const HANDS = [" in src and "const LEGS = [" in src, "手(HANDS)・脚(LEGS)が定義されている")
    check('hands: "手"' in src and 'legs: "脚"' in src, "装備スロット名に 手/脚 がある")

    # --- 身を守る / 守護撤廃 ---
    check('label: "身を守る"' in src, "戦闘コマンド「身を守る」が残っている")
    guard_effects = re.findall(r"[{,]\s*guard:\s*\d", src)
    check(not guard_effects, "効果データに guard(守護)が残っていない: %d 件" % len(guard_effects))

    # --- ツリー ---
    check("parentsOf(n).some" not in src.split("function nodeState")[1][:700], "パッシブツリーの接続制限が撤廃されている")
    check("const TREE_GATE = { n: 4, k: 12 }" in src, "ノータブル/キーストーンの解放条件(累計Pt)がある")
    for name in ["レゾリュートテクニック", "バルワーク", "ブラッドマジック", "ダンスウィズデス", "ヴァール・パクト"]:
        check(name in src, "キーストーン「%s」がある" % name)

    # --- キーストーン効果キー ---
    for key in ["leech", "deflect", "bloodmagic", "bulwark", "dwd", "resolute", "hdef", "ldef"]:
        check(re.search(r"\b%s\b" % key, src) is not None, "効果キー %s が実装されている" % key)

    # --- 武器・スキル ---
    for w in ["短弓", "短銃", "苦無", "手裏剣", "銃"]:
        check('["%s", "skl"' % w in src, "武器種 %s が器用さ依存" % w)
    check(len(re.findall(r'\[\d+, \d+, \d+, "skl"\]', src)) >= 5, "ゲージスキル5種が器用さ修正になっている")

    check("window.__RAG" in src and "test=1" in src, "?test=1 の入口(window.__RAG)がある")

    # --- 難易度 ---
    m = re.search(r"const HARD_HP = ([\d.]+), HARD_DMG = ([\d.]+)", src)
    check(bool(m), "HARD_HP / HARD_DMG が定義されている")
    if m:
        print("       HARD_HP=%s HARD_DMG=%s" % m.groups())
        check(float(m.group(1)) >= 2.0 and float(m.group(2)) >= 1.7, "難易度倍率が HP>=2.0 / DMG>=1.7")


def dom_checks(path):
    print("[画面(DOM)チェック]")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("playwright が未インストールのため画面チェックを省略 (pip install playwright && playwright install chromium)")
        return
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 420, "height": 860})
        page.set_default_timeout(8000)
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
        # 外部リソース(フォント等)の読み込み失敗はネットワーク環境次第なので無視する
        page.on("console", lambda m: errors.append("console.error: %s" % m.text)
                if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(path.resolve().as_uri())
        page.wait_for_timeout(800)

        # タイトル画面
        check(page.locator("#choices button").count() >= 3, "タイトル画面に選択肢がある")
        check(page.locator("#xpBar").count() == 0, "#xpBar が存在しない")

        # 開始
        start = page.get_by_role("button", name=re.compile("旅立つ"))
        if start.count() == 0:
            warn("「旅立つ」ボタンが見つからない(ボタン名が変わった可能性)")
        else:
            start.first.click()
            page.wait_for_timeout(600)
            check(page.locator("#hud").is_visible(), "開始後に HUD が表示される")
            check(page.locator(".vital").count() == 1, "HP/MP の .vital ブロックがある")

            # ステータス画面
            page.locator("#statBtn").click()
            page.wait_for_timeout(300)
            body = page.locator("#ovBody").inner_text()
            check("器用さ" in body, "ステータス画面に「器用さ」がある")
            check("経験値" in body, "ステータス画面に「経験値」がある")
            page.locator("#ovClose").click()

            # パッシブ画面
            page.locator("#treeBtn").click()
            page.wait_for_timeout(500)
            check(page.locator("#ovBody").inner_text() != "", "パッシブ画面が開ける")
            page.locator("#ovClose").click()

            # 戦闘まで進んで HUD を確認(到達できなければ警告のみ)
            reached = False
            for _ in range(25):
                if page.locator("body.fighting").count():
                    reached = True
                    break
                # 確認ポップアップ(.cf-ov)が出ているとボタンが押せないので、先に閉じる
                if page.locator(".cf-ov").count():
                    ok = page.locator(".cf-ov .cf-ok:not([disabled])")
                    try:
                        (ok if ok.count() else page.locator(".cf-ov .cf-no")).first.click(timeout=3000)
                    except Exception:
                        page.evaluate("document.querySelectorAll('.cf-ov').forEach(e => e.remove())")
                    page.wait_for_timeout(150)
                    continue
                btns = page.locator("#choices button:not([disabled])")
                if btns.count() == 0:
                    page.wait_for_timeout(300)
                    continue
                try:
                    btns.first.click(timeout=3000)
                except Exception:
                    page.evaluate("document.querySelectorAll('.cf-ov').forEach(e => e.remove())")
                page.wait_for_timeout(250)
            if reached:
                check(not page.locator("#statsLine").is_visible(), "戦闘中に statsLine が非表示")
                check(not page.locator("#gearLine").is_visible(), "戦闘中に gearLine が非表示")
            else:
                warn("戦闘まで到達できなかった(戦闘中HUDの確認を省略)")
        browser.close()
    check(not errors, "ページエラー/コンソールエラーが無い" + ("" if not errors else ": " + " | ".join(errors[:3])))


def hook_checks(path):
    """?test=1 で公開される window.__RAG を使って、効果の数値を直接確認する。"""
    print("[内部値チェック (?test=1)]")
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("playwright が未インストールのため内部値チェックを省略")
        return
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 420, "height": 860})
        page.set_default_timeout(8000)
        page.on("pageerror", lambda e: errors.append("pageerror: %s" % e))
        page.goto(path.resolve().as_uri() + "?test=1")
        page.wait_for_timeout(800)
        check(page.evaluate("typeof window.__RAG") == "object", "?test=1 で window.__RAG が公開される")
        plain = browser.new_page()
        plain.goto(path.resolve().as_uri())
        plain.wait_for_timeout(300)
        check(plain.evaluate("typeof window.__RAG") == "undefined", "?test=1 が無いときは公開されない")
        start = page.get_by_role("button", name=re.compile("旅立つ"))
        if start.count() == 0:
            warn("「旅立つ」が見つからず内部値チェックを省略")
            browser.close()
            return
        start.first.click()
        page.wait_for_timeout(600)
        r = page.evaluate("""() => {
          const R = window.__RAG, G = R.G, out = {};
          out.skl = G.skl;
          out.critBase = R.critMin();
          const d0 = R.armDef();
          G.hands = { n: "t", def: 3, b: {} }; G.legs = { n: "t", def: 2, b: {} };
          out.defGain = R.armDef() - d0;
          G.hands = null; G.legs = null;
          const keys = ["leech", "deflect", "bloodmagic", "bulwark", "dwd", "resolute"];
          out.before = keys.map((k) => R.T(k));
          keys.forEach((k) => G.traits.push({ key: k }));
          out.after = keys.map((k) => R.T(k));
          out.critResolute = R.critMin();
          return out;
        }""")
        check(isinstance(r["skl"], (int, float)) and r["skl"] == r["skl"], "新規ランの G.skl が数値 (%s)" % r["skl"])
        check(12 <= r["critBase"] <= 20, "critMin() が 12〜20 (%s)" % r["critBase"])
        check(r["defGain"] == 5, "手・脚の防具が防御に反映される (+%s)" % r["defGain"])
        check(all(v == 0 for v in r["before"]), "効果キーは初期状態で 0")
        check(all(v == 1 for v in r["after"]), "traits から効果キーが数えられる")
        check(r["critResolute"] == 99, "レゾリュートテクニックで会心が出なくなる (critMin=99)")
        r2 = page.evaluate("""() => {
          const R = window.__RAG; const out = {};
          const hp = [];
          for (let i = 0; i < 8; i++) { const e = R.makeEnemy(false, false); hp.push(e.hp); }
          out.hp = Math.min(...hp);
          out.atk = R.makeEnemy(false, false).atk;
          return out;
        }""")
        check(r2["hp"] > 0, "makeEnemy が敵を作れる (HP最小 %s)" % r2["hp"])
        browser.close()
    check(not errors, "内部値チェック中にページエラーが無い" + ("" if not errors else ": " + " | ".join(errors[:3])))


def main():
    if not HTML or not Path(HTML).exists():
        print("ゲームHTMLが見つかりません。引数で指定してください: python tests/smoke_extra.py path/to/index.html")
        return 2
    print("対象:", HTML)
    src = Path(HTML).read_text(encoding="utf-8")
    static_checks(src)
    dom_checks(Path(HTML))
    hook_checks(Path(HTML))
    print("\n結果: 失敗 %d / 警告 %d" % (len(failures), len(warnings)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
