"""US-05, US-06, US-07 — checkout."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "alice")


async def run(d):
    P = d.page
    await d.goto("/cart", wait=1.2)
    d.cap("購物車：寵物床 1 件、主食罐 3 罐", "Cart: one pet bed and three cans")
    await d.wait(1.5)
    await d.click(P.get_by_role("button", name="結帳"), after=2.0)

    d.cap("結帳頁列出小計、折扣、稅、運費與總額", "Checkout shows subtotal, discounts, tax, shipping, total")
    await d.scroll_to(P.get_by_role("heading", name="金額明細"), after=1.0)
    await d.highlight(P.get_by_role("heading", name="金額明細").locator(".."), sec=3.0)

    d.cap("有效期內的折扣自動套用：買 2 送 1、兩檔季節折扣", "Active discounts apply: buy 2 get 1 plus two seasonal")
    await d.wait(3.5)

    d.cap("確認付款後建立訂單，狀態為 received", "After payment the order is created as “received”")
    await d.click(P.get_by_role("button", name="確認付款"), after=3.0)
    d.cap("同一筆交易中扣庫存、清空購物車", "Stock is deducted and the cart cleared in one transaction")
    await d.wait(3.0)
    d.end_cap()
