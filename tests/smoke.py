"""スモークテスト: 起動→拠点選択→戦闘→パッシブ割り振りまで。JSエラーが出たら失敗。"""
import asyncio, sys, pathlib
from playwright.async_api import async_playwright
URL = pathlib.Path(__file__).resolve().parent.parent.joinpath("game/index.html").as_uri()
IGNORE = ("ERR_NAME_NOT_RESOLVED", "ERR_INTERNET_DISCONNECTED")

async def main():
    errs, fails = [], []
    async with async_playwright() as p:
        b = await p.chromium.launch(args=["--autoplay-policy=no-user-gesture-required"])
        pg = await b.new_page(viewport={"width": 390, "height": 844})
        pg.on("pageerror", lambda e: errs.append(str(e)))
        pg.on("console", lambda m: errs.append(m.text) if m.type == "error" and not any(i in m.text for i in IGNORE) else None)
        await pg.goto(URL); await pg.wait_for_timeout(500)
        await pg.locator("#choices button", has_text="旅立つ").first.click()
        if "★" not in await pg.locator("#choices").inner_text(): fails.append("拠点選択が出ない")
        await pg.locator("#choices button").nth(0).click()
        fought = False
        for _ in range(500):
            if await pg.locator("#choices.battle").count(): fought = True
            # 購入・装備などの確認ポップアップ(.cf-ov)が出たら先に閉じる(出たままだとボタンが押せずタイムアウトする)
            if await pg.locator(".cf-ov").count():
                ok = pg.locator(".cf-ov .cf-ok:not([disabled])")
                if await ok.count(): await ok.first.click()
                else: await pg.locator(".cf-ov .cf-no").first.click()
                await pg.wait_for_timeout(120)
                continue
            bt = pg.locator("#choices button:not([disabled])")
            if await bt.count(): await bt.first.click()
            await pg.wait_for_timeout(120)
            if "パッシブ (" in await pg.locator("#treeBtn").inner_text() and fought: break
        if not fought: fails.append("戦闘に入れない")
        hp = await pg.locator("#hpNum").inner_text()
        if "," not in hp: fails.append("HPが100倍になっていない: " + hp)
        await pg.evaluate("document.querySelectorAll('.cf-ov').forEach(e=>e.remove())")
        await pg.locator("#treeBtn").click()
        if await pg.locator("g.tn").count() != 190: fails.append("ツリーのノード数が190でない")
        for i in range(1, 6):
            await pg.locator(".tr-tab").nth(i).click()
            if await pg.locator("g.tn").count() != 190: fails.append("系統ジャンプ後にマップが壊れた")
        await pg.locator(".tr-tab").nth(0).click()
        if await pg.locator("g.tn.st-open").count():
            await pg.locator("g.tn.st-open").first.click(force=True)
            if await pg.locator(".cf-box").count() == 0: fails.append("ノードをタップしても詳細が出ない")
            else: await pg.locator(".cf-ok").click()
        # タイトルからの閲覧
        await pg.goto(URL); await pg.wait_for_timeout(400)
        await pg.locator("#choices button", has_text="パッシブツリーを見る").first.click()
        if await pg.locator("g.tn").count() != 190: fails.append("タイトルからツリーが開けない")
        await b.close()
    for e in errs: fails.append("JSエラー: " + e)
    print("FAIL" if fails else "OK", *fails, sep="\n")
    sys.exit(1 if fails else 0)
asyncio.run(main())
