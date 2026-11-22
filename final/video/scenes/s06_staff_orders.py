"""US-13, US-14 — staff process orders and review returns."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login

ORDER_ID = 14   # the order alice placed in s03 (after ./start.sh reset)


async def setup(page, base):
    await login(page, base, "staff")


async def run(d):
    P = d.page
    await d.goto("/staff/orders", wait=1.5)
    d.cap("訂單管理：查看新進的訂單", "Order management: new orders come in")
    await d.select(P.get_by_label("狀態"), "received")
    await d.click(P.get_by_role("button", name="搜尋"), after=1.5)
    await d.click(P.locator("tr", has_text=f"#{ORDER_ID}").first, after=1.5)

    d.cap("訂單狀態只能依序前進：processing → shipping → closed", "Status moves forward only: processing → shipping → closed")
    btn = P.get_by_role("button", name=re.compile("推進到下一狀態"))
    for _ in range(3):
        await d.click(btn, after=1.0)
        foot = P.locator(".bo-modal__foot")
        if await foot.count():
            await d.click(foot.get_by_role("button").last, after=1.6)

    d.cap("每次變更都由 trigger 自動寫入狀態歷程", "Each change is logged by a trigger in the status history")
    await d.scroll_to(P.get_by_role("heading", name="狀態歷程"), after=0.6)
    await d.highlight(P.get_by_role("heading", name="狀態歷程").locator(".."), sec=2.8)

    d.cap("審核顧客的退貨申請", "Review customers’ return requests")
    await d.click(P.get_by_role("link", name="↩️ 退貨審核"), after=1.2)
    await d.select(P.get_by_label("狀態"), "pending", after=1.2)
    await d.click(P.locator("tr", has_text="#3").first, after=1.5)

    d.cap("核准後依 BR-26 計算退款，並回補庫存", "Approval computes the refund (BR-26) and restocks")
    await d.click(P.get_by_role("button", name="核准退貨"), after=1.0)
    foot = P.locator(".bo-modal__foot")
    if await foot.count():
        await d.click(foot.get_by_role("button").last, after=2.5)
    await d.wait(1.5)
    d.end_cap()
