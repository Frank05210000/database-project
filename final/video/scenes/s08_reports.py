"""US-17, US-18 — sales reports (views V1, V2)."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "staff")


async def run(d):
    P = d.page
    await d.goto("/staff/reports", wait=2.0)
    d.cap("各商店的日銷售報表：日期、商店、訂單數、銷售總額", "Daily sales per store: date, store, orders, total")
    await d.wait(2.0)
    await d.scroll(520, after=1.5)

    d.cap("切換成週報、月報", "Switch to weekly and monthly reports")
    await d.scroll(-520, after=0.6)
    await d.click(P.locator("button.bo-tab", has_text="週"), after=2.0)
    await d.click(P.locator("button.bo-tab", has_text="月"), after=2.0)

    d.cap("熱銷商品 Top 10：依銷售數量排名", "Top 10 best sellers by quantity sold")
    top = P.get_by_text("熱銷商品 Top 10").first
    await d.scroll_to(top, after=0.8)
    await d.highlight(top.locator("xpath=ancestor::*[contains(@class,'bo-card')][1]"), sec=3.0)
    d.end_cap()
