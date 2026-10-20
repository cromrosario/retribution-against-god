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


async def step_overlays(pg):
    """演出・確認ポップアップが出ていたら処理する。処理したら True"""
    if await pg.locator(".cf-ov").count():  # 購入・装備などの確認
        ok = pg.locator(".cf-ov .cf-ok:not([disabled])")
        if await ok.count(): await ok.first.click()
        else: await pg.locator(".cf-ov .cf-no").first.click()
        return True
    if await pg.locator("#dice").count():  # d20 / 2D6 判定の演出(確定後はタップで閉じる)
        await pg.locator("#dice").click(); return True
    if await pg.locator(".rare-ov").count():  # レアドロップ演出
        await pg.locator(".rare-ov").click(); return True
    if await pg.locator("#ov:not([hidden])").count():  # 持ち物・ステータスなどの重ね表示
        await pg.locator("#ovClose").click(); return True
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
            if await step_overlays(pg): await pg.wait_for_timeout(120); continue
            bt = pg.locator("#choices button:not([disabled])")
            if await bt.count(): await bt.first.click()
            await pg.wait_for_timeout(120)
            if await pg.locator(".banner.lv").count() or "レベルが上がった" in await pg.locator("#log").inner_text(): leveled = True
            if fought and leveled: break
        if not fought: fails.append("戦闘に入れない")
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
                bt = pg.locator("#choices button:not([disabled])")
                if await bt.count(): await bt.first.click()
            await pg.wait_for_timeout(120)
        info.append(f"イベント部屋 {events}回 / 挿絵を観測 {seen_art}回 / 2D6演出を観測 {seen_d6}回")
        if events >= 5 and seen_art == 0: fails.append("イベント部屋に入っているのに挿絵が一度も出ない")

        # タイトルへ戻る: 背景がタイトル絵に戻る
        await pg.goto(URL); await pg.wait_for_timeout(400)
        if await pg.evaluate("document.documentElement.hasAttribute('data-zbg')"): fails.append("タイトルで拠点背景が残っている")
        await b.close()

    for e in errs: fails.append("JSエラー: " + e)
    print("FAIL" if fails else "OK", *fails, *("INFO: " + i for i in info), sep="\n")
    sys.exit(1 if fails else 0)

asyncio.run(main())
