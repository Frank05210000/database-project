"""US-03, US-04 — login and shopping cart."""


async def run(d):
    P = d.page
    await d.goto("/login")
    d.cap("顧客用 loginid 與密碼登入", "The customer logs in with loginid and password")
    await d.type(P.get_by_label("帳號", exact=True), "alice", delay=120)
    await d.type(P.get_by_label("密碼", exact=True), "customer123", delay=90)
    await d.click(P.get_by_role("button", name="登入", exact=True), after=2.0)

    d.cap("把商品加入購物車：主食罐買 2 送 1，買 3 罐", "Add to cart: canned food is buy 2 get 1")
    await d.goto("/product/5", wait=1.0)
    await d.click(P.get_by_role("button", name="+", exact=True), after=0.5)
    await d.click(P.get_by_role("button", name="+", exact=True), after=0.8)
    await d.click(P.get_by_role("button", name="🛒 加入購物車"), after=2.2)

    d.cap("數量不能超過庫存：輸入 20，系統限制為庫存 9", "Quantity is capped at the stock: 20 becomes 9")
    await d.goto("/product/14", wait=1.0)
    await d.fill(P.locator("input[type=number]").first, "20", after=0.8)
    await d.press("Tab", after=1.0)
    await d.highlight(P.get_by_text("庫存", exact=False).first, sec=2.2)

    d.cap("在購物車調整數量，或移除不要的商品", "Adjust quantities or remove items in the cart")
    await d.goto("/cart", wait=1.5)
    item = P.locator(".cart-page__item", has_text="羽毛逗貓棒")
    await d.click(item.get_by_role("button", name="刪除"), after=2.5)
    d.end_cap()
