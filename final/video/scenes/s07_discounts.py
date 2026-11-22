"""US-15, US-16 — discount policies; overlapping special events are rejected (BR-13)."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "staff")


async def run(d):
    P = d.page
    M = P.locator(".bo-modal")
    await d.goto("/staff/discounts", wait=1.5)
    d.cap("三種折扣：運費、季節性、特殊活動", "Three kinds: shipping, seasonal, special event")
    await d.wait(2.0)

    d.cap("新增季節性折扣，代碼由系統產生", "Create a seasonal discount; the system assigns the code")
    await d.click(P.get_by_role("button", name="＋ 新增折扣"), after=1.0)
    await d.select(M.get_by_label(re.compile("^折扣類型")), "seasonal")
    await d.type(M.get_by_label(re.compile("^說明")), "聖誕節全館 85 折", delay=120)
    await d.fill(M.get_by_label(re.compile("^開始日期")), "2026-12-20")
    await d.fill(M.get_by_label(re.compile("^結束日期")), "2026-12-26")
    await d.type(M.get_by_label(re.compile("^折抵百分比")), "15", delay=150)
    await d.click(M.get_by_role("button", name="儲存"), after=2.5)
    await d.highlight(P.locator("tr", has_text="聖誕節全館").first, sec=2.0)

    d.cap("貓抓板跳台已有 11/1–12/31 的特殊活動", "The cat tower already has an event (Nov 1 – Dec 31)")
    await d.highlight(P.locator("tr", has_text="EVT-0001").first, sec=2.5)

    d.cap("再新增一個期間重疊的特殊活動……", "Now add another, overlapping special event…")
    await d.click(P.get_by_role("button", name="＋ 新增折扣"), after=1.0)
    await d.select(M.get_by_label(re.compile("^折扣類型")), "special_event")
    await d.type(M.get_by_label(re.compile("^說明")), "跳台聖誕加碼 7 折", delay=120)
    await d.fill(M.get_by_label(re.compile("^開始日期")), "2026-12-20")
    await d.fill(M.get_by_label(re.compile("^結束日期")), "2026-12-25")
    pct = M.get_by_label(re.compile("^折抵百分比"))
    if not await pct.count():
        await d.click(M.get_by_text("折扣率", exact=True))
    await d.type(M.get_by_label(re.compile("^折抵百分比")), "30", delay=150)
    await d.type(M.get_by_placeholder("篩選商品名稱或商店"), "貓抓板", delay=150)
    await d.check(M.locator(".bo-multi label", has_text="貓抓板跳台").locator("input"))
    await d.click(M.get_by_role("button", name="儲存"), after=2.0)

    d.cap("期間重疊，被 BR-13 的 trigger 拒絕", "Rejected by the BR-13 trigger: periods overlap")
    await d.wait(3.5)
    d.end_cap()
