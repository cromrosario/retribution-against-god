"""スモークテスト: 起動→拠点選択→戦闘→レベルアップ→イベント部屋の探索。JSエラーが出たら失敗。
パッシブツリー削除後の版。TRPGイベント・UIスキン・ボス画像・拠点背景・難易度の組み込みも確認する。
"""
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
HTML = pathlib.Path(__file__).resolve().parent.parent.joinpath("game/index.html")
URL = HTML.as_uri()
IGNORE = ("ERR_NAME_NOT_RESOLVED", "ERR_INTERNET_DISCONNECTED")

# 組み込みの静的チェック(マーカーと接続箇所が1件ずつあること / 削除したものが無いこと)
MUST_ONCE = [
    "==== TRPG:BEGIN", "==== EVIMG:BEGIN", "==== SKIN:BEGIN", "==== SKIN-JS:BEGIN",
    "==== BOSSIMG:BEGIN", "==== ZBG:BEGIN", "==== ZBG-CSS:BEGIN", "==== DIFF:BEGIN",
    "v += pactB(k);", "if (trpgRun()) return;", "trpgStatus(b);", "tuneEnemy(enemy);",
    "zoneBg(z);", "zoneBg(-1);", "bossArtLog(enemy.key)",
]
MUST_NOT = ["treeB", "#treeBtn", "TREE_BY", "パッシブツリー"]


TRACE = []  # (段階, 手番, 操作, 層表示)


async def state(pg):
    """いまの画面の要約(失敗時に表示する)"""
    js = """() => {
      const t = (q) => { const e = document.querySelector(q); return e ? e.innerText.replace(/\\s+/g, ' ').slice(0, 300) : '(なし)'; };
      const ov = ['.cf-ov', '#dice', '.rare-ov', '.d6-ov', '.dice-ov', '.banner'].filter((q) => document.querySelector(q));
      const btns = [...document.querySelectorAll('#choices button')].map((b) => (b.disabled ? '[無効]' : '') + b.innerText.replace(/\\s+/g, ' ').slice(0, 40));
      const top = (() => { const b = document.querySelector('#choices button'); if (!b) return '(ボタンなし)';
        const r = b.getBoundingClientRect(); const e = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
        return e ? (e.tagName + '#' + e.id + '.' + e.className).slice(0, 80) : '(画面外)'; })();
      return { body: document.body.className, choicesClass: (document.querySelector('#choices') || {}).className,
        floor: t('#floorLabel'), choices: btns, overlays: ov, ovHidden: (document.querySelector('#ov') || {}).hidden,
        topAtFirstButton: top, log: t('#log') };
    }"""
    return await pg.evaluate(js)


EXIT_WORDS = ("鍛冶場を出る", "立ち去る")      # 店・鍛冶場・イベントから抜けるボタン(優先して押す)
AVOID_WORDS = ("ボーナスを打ち直す", "を鍛える")  # 押すと同じ画面に戻ってループするボタン


async def pick(pg):
    """押すボタンを選ぶ。戦闘中は先頭(コンボ)、それ以外は『出る』系を優先し、ループするボタンは避ける。"""
    bt = pg.locator("#choices button:not([disabled])")
    n = await bt.count()
    if n == 0: return None
    if await pg.locator("#choices.battle").count(): return bt.first
    texts = [t.replace("\n", " ") for t in await bt.all_inner_texts()]
    for w in EXIT_WORDS:
        for i, t in enumerate(texts):
            if w in t: return bt.nth(i)
    for i, t in enumerate(texts):
        if not any(w in t for w in AVOID_WORDS): return bt.nth(i)
    return bt.first


async def tap(pg, sel):
    """演出は自動で消えることがある。クリック直前に消えても失敗にしない"""
    try: await pg.locator(sel).first.click(timeout=1500)
    except Exception: pass


async def step_overlays(pg):
    """演出・確認ポップアップが出ていたら処理する。処理したら True"""
    if await pg.locator(".cf-ov").count():  # 購入・装備などの確認
        ok = pg.locator(".cf-ov .cf-ok:not([disabled])")
        await tap(pg, ".cf-ov .cf-ok:not([disabled])" if await ok.count() else ".cf-ov .cf-no")
        return True
    if await pg.locator("#dice").count():  # d20 / 2D6 判定の演出(確定後はタップで閉じる)
        await tap(pg, "#dice"); return True
    if await pg.locator(".rare-ov").count():  # レアドロップ演出
        await tap(pg, ".rare-ov"); return True
    if await pg.locator("#ov:not([hidden])").count():  # 持ち物・ステータスなどの重ね表示
        await tap(pg, "#ovClose"); return True
    return False


async def main():
    errs, fails, info = [], [], []
    src = HTML.read_text(encoding="utf-8")
    for s in MUST_ONCE:
        if src.count(s) != 1: fails.append(f"組み込み不足: '{s}' が {src.count(s)}件(期待 1)")
    for s in MUST_NOT:
        if s in src: fails.append(f"削除漏れ: '{s}' が残っている")

    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.set_default_timeout(10000)
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and not any(i in m.text for i in IGNORE) else None)
        await pg.goto(URL); await pg.wait_for_timeout(500)

        # タイトル: ツリーの入口が無いこと
        if await pg.locator("#choices button", has_text="パッシブツリー").count(): fails.append("タイトルにツリーの入口が残っている")
        await pg.locator("#choices button", has_text="旅立つ").first.click()
        if "★" not in await pg.locator("#choices").inner_text(): fails.append("拠点選択が出ない")
        await pg.locator("#choices button").nth(0).click()
        await pg.wait_for_timeout(200)
        if not await pg.evaluate("document.documentElement.hasAttribute('data-zbg')"): fails.append("拠点の背景が切り替わらない")
        if await pg.locator("#treeBtn").count(): fails.append("パッシブボタンが残っている")

        # 第1段階: 戦闘してレベルが上がるまで
        # この版のHUDにはレベル表示が無いので、レベルアップの演出(.banner.lv)かログの文言で検知する
        fought = leveled = False
        for _ in range(500):
            if await pg.locator("#choices.battle").count(): fought = True
            if await step_overlays(pg): TRACE.append(("1", _, "(演出/確認を閉じた)", "")); await pg.wait_for_timeout(120); continue
            bt = await pick(pg)
            if bt is not None:
                TRACE.append(("1", _, (await bt.inner_text()).replace("\n", " ")[:30], (await pg.locator("#floorLabel").inner_text()).replace("\n", " ")[:20]))
                await bt.click()
            else:
                TRACE.append(("1", _, "(押せるボタンなし)", ""))
            await pg.wait_for_timeout(120)
            if await pg.locator(".banner.lv").count() or "レベルが上がった" in await pg.locator("#log").inner_text(): leveled = True
            if fought and leveled: break
        if not fought:
            fails.append("戦闘に入れない")
            fails.append("状態: " + str(await state(pg)))
            fails.append("直近の操作: " + str(TRACE[-15:]))
            await pg.screenshot(path=str(pathlib.Path(__file__).resolve().parent / "smoke_fail.png"), full_page=True)
        if not leveled: fails.append("レベルが上がらない")
        hp = await pg.locator("#hpNum").inner_text()
        if "," not in hp: fails.append("HPが100倍になっていない: " + hp)

        # ステータス画面: 契約・探索の記録の欄があり、ツリー欄が無い
        await pg.evaluate("document.querySelectorAll('.cf-ov,#dice,.rare-ov').forEach(e=>e.remove())")
        if await pg.locator("#statBtn").is_visible():
            await pg.locator("#statBtn").click()
            body = await pg.locator("#ovBody").inner_text()
            if "契約" not in body or "探索の記録" not in body: fails.append("ステータス画面に契約・探索の記録が無い")
            if "パッシブツリー" in body: fails.append("ステータス画面にツリー欄が残っている")
            await pg.locator("#ovClose").click()

        # 第2段階: 「何かが待つ部屋」を優先して探索し、TRPGイベントの演出を観測する
        seen_d6 = seen_art = events = 0
        for _ in range(600):
            if await pg.locator(".d6-ov").count(): seen_d6 += 1
            if await pg.locator("#log .ev-art").count(): seen_art += 1
            if await step_overlays(pg): await pg.wait_for_timeout(120); continue
            door = pg.locator("#choices.doors button:not([disabled])", has_text="何かが待つ部屋")
            if await door.count():
                events += 1; await door.first.click()
            else:
                bt = await pick(pg)
                if bt is not None: await bt.click()
            await pg.wait_for_timeout(120)
        info.append(f"イベント部屋 {events}回 / 挿絵を観測 {seen_art}回 / 2D6演出を観測 {seen_d6}回")
        if events >= 5 and seen_art == 0: fails.append("イベント部屋に入っているのに挿絵が一度も出ない")

        # タイトルへ戻る: 背景がタイトル絵に戻る
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.evaluate("document.documentElement.hasAttribute('data-zbg')"): fails.append("タイトルで拠点背景が残っている")
        await b.close()

    for e in errs: fails.append("JSエラー: " + e)
    if fails and TRACE: info.append("操作数: " + str(len(TRACE)) + " / 最初の5手: " + str(TRACE[:5]))
    print("FAIL" if fails else "OK", *fails, *("INFO: " + i for i in info), sep="\n")
    sys.exit(1 if fails else 0)

asyncio.run(main())
