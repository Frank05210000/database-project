"""US-01, US-02 — guest search and registration."""


async def run(d):
    P = d.page
    await d.goto("/")
    d.cap("訪客不用登入，就能用關鍵字搜尋商品", "Guests can search by keyword without logging in")
    await d.type(P.get_by_placeholder("搜尋商品名稱或說明…"), "貓", delay=250)
    await d.click(P.get_by_role("button", name="🔍 搜尋"), after=2.2)

    d.cap("商品頁顯示價格、庫存、所屬商店與活動折扣", "Product pages show price, stock, store and event discount")
    await d.click(P.locator(".product-card__name", has_text="貓抓板跳台"), after=2.5)
    await d.scroll(260, after=2.0)

    d.cap("想購買時，先註冊成為顧客", "To buy, a guest first registers as a customer")
    await d.goto("/login", wait=0.8)
    await d.click(P.get_by_text("立即註冊"), after=1.0)
    await d.type(P.get_by_label("帳號", exact=True), "alice", delay=120)
    await d.type(P.get_by_label("姓名", exact=True), "王小丹", delay=120)
    await d.type(P.get_by_label("密碼", exact=True), "demo1234", delay=90)
    await d.type(P.get_by_label("電子信箱"), "dan@example.com", delay=50)
    await d.type(P.get_by_label("地址"), "台北市大安區忠孝東路三段 1 號", delay=40)

    d.cap("loginid 重複時，資料庫的 UNIQUE 限制會拒絕", "A duplicate loginid is rejected by UNIQUE")
    await d.click(P.get_by_role("button", name="註冊並登入"), after=3.0)

    d.cap("換一個 loginid 就能註冊並登入", "With a new loginid, registration succeeds")
    await d.type(P.get_by_label("帳號", exact=True), "demo_dan", delay=120)
    await d.click(P.get_by_role("button", name="註冊並登入"), after=3.0)
    d.end_cap()
