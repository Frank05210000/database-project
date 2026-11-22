# 擷取 Section 6 的 GUI 截圖（只瀏覽、不修改資料）。需要系統已用 ./start.sh 啟動。
# 用法：python3 tools/gui_shots.py [輸出資料夾，預設 img]
import sys, os
from playwright.sync_api import sync_playwright

BASE = "http://localhost:5173"
OUT = sys.argv[1] if len(sys.argv) > 1 else "img"
os.makedirs(OUT, exist_ok=True)

SHOTS = {
    None: [("gui_home", "/"), ("gui_product", "/product/1"), ("gui_stores", "/stores"), ("gui_login", "/login")],
    ("alice", "customer123"): [("gui_cart", "/cart"), ("gui_my_orders", "/my-orders"), ("gui_order_detail", "/order/5")],
    ("staff", "staff123"): [("gui_staff_products", "/staff/products"), ("gui_staff_orders", "/staff/orders"),
                            ("gui_staff_order_detail", "/staff/orders/10"), ("gui_staff_returns", "/staff/returns"),
                            ("gui_staff_discounts", "/staff/discounts"), ("gui_staff_reports", "/staff/reports"),
                            ("gui_staff_dashboard", "/staff")],
    ("staff_xinyi", "staff123"): [("gui_store_staff_products", "/staff/products")],
    ("admin", "admin123"): [("gui_admin_users", "/admin/users"), ("gui_admin_stores", "/admin/stores")],
}
MOBILE = [("gui_mobile_home", "/"), ("gui_mobile_product", "/product/1")]   # 手機版（375×812）

FULL = {"gui_cart"}   # 購物車內容較長，截整頁

with sync_playwright() as p:
    browser = p.chromium.launch(channel="chrome")
    for acct, pages in SHOTS.items():
        ctx = browser.new_context(viewport={"width": 1280, "height": 800}, device_scale_factor=1.5, locale="zh-TW")
        pg = ctx.new_page()
        if acct:
            pg.goto(BASE + "/login"); pg.wait_for_load_state("load"); pg.wait_for_timeout(1000)
            inputs = pg.locator("input")
            inputs.nth(0).fill(acct[0]); inputs.nth(1).fill(acct[1]); inputs.nth(1).press("Enter")
            pg.wait_for_timeout(1500)
        for name, path in pages:
            pg.goto(BASE + path); pg.wait_for_load_state("load"); pg.wait_for_timeout(2000)
            f = f"{OUT}/{name}.png"
            pg.screenshot(path=f, full_page=name in FULL)
            print(f, pg.url)
        ctx.close()
    ctx = browser.new_context(viewport={"width": 375, "height": 812}, device_scale_factor=2, locale="zh-TW", is_mobile=True, has_touch=True)
    pg = ctx.new_page()
    for name, path in MOBILE:
        pg.goto(BASE + path); pg.wait_for_load_state("load"); pg.wait_for_timeout(2000)
        pg.screenshot(path=f"{OUT}/{name}.png"); print(name, pg.url)
    ctx.close()
    browser.close()
