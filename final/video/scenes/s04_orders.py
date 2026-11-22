"""US-08 ~ US-11 — order history, cancel, return request, store review."""
import pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "alice")


async def run(d):
    P = d.page
    await d.goto("/my-orders", wait=1.2)
    d.cap("顧客可以查詢歷史訂單與目前狀態", "Customers can view past orders and their status")
    await d.scroll(400, after=1.2)
    await d.scroll(-400, after=0.8)

    d.cap("訂單 #12 還是 received，可以直接取消", "Order #12 is still “received”, so it can be cancelled")
    card = P.locator(".order-card", has_text="#12").first
    await d.click(card.get_by_role("button", name="查看詳情"), after=1.5)
    await d.highlight(P.get_by_role("heading", name="訂單進度").locator(".."), sec=1.8)
    await d.click(P.get_by_role("button", name="取消訂單"), after=2.5)

    d.cap("已完成的訂單只能申請退貨：選商品與數量", "Completed orders allow a return: pick items and quantity")
    await d.goto("/order/3", wait=1.2)
    await d.click(P.get_by_role("button", name="申請退貨"), after=1.0)
    await d.fill(P.locator("input[type=number]").first, "1", after=0.6)
    await d.type(P.get_by_placeholder("請說明退貨原因"), "尺寸不合，想退一件", delay=120)
    await d.click(P.get_by_role("button", name="送出退貨申請"), after=2.5)

    d.cap("每筆訂單只能申請一次退貨，等待工作人員審核", "One return per order, pending staff review")
    await d.wait(2.0)

    d.cap("訂單完成後可以替商店評分與評論", "After completion, customers can rate the store")
    await d.scroll_to(P.get_by_role("heading", name="評價商店"), after=0.8)
    await d.select(P.get_by_label("評分"), "5")
    await d.type(P.get_by_label("評論（選填）"), "出貨很快，包裝很用心！", delay=110)
    await d.click(P.get_by_role("button", name="送出評價"), after=2.5)
    d.end_cap()
