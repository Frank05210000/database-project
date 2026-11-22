"""US-12 — staff manage products and stock."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "staff")


async def run(d):
    P = d.page
    M = P.locator(".bo-modal")
    await d.goto("/staff", wait=1.5)
    d.cap("工作人員登入後進入管理後台", "Staff log in to the back office")
    await d.wait(1.5)
    await d.click(P.get_by_role("link", name="📦 商品與庫存"), after=1.5)

    d.cap("新增商品：選商店、類別，填價格與庫存", "Create a product: store, category, price, stock")
    await d.click(P.get_by_role("button", name="＋ 新增商品"), after=1.0)
    await d.select(M.get_by_label(re.compile("^商店")), "1")
    await d.select(M.get_by_label(re.compile("^類別")), "toy")
    await d.type(M.get_by_label(re.compile("^商品名稱")), "聖誕麋鹿玩偶", delay=130)
    await d.type(M.get_by_label(re.compile("^商品描述")), "耶誕限定款，柔軟耐咬。", delay=60)
    await d.type(M.get_by_label(re.compile("^價格")), "299", delay=120)
    await d.type(M.get_by_label(re.compile("^庫存")), "30", delay=120)
    await d.click(M.get_by_role("button", name="/images/hat.webp"), after=0.6)
    await d.click(M.get_by_role("button", name="儲存"), after=2.2)

    d.cap("修改價格與庫存", "Update its price and stock")
    r = P.locator("tr", has_text="聖誕麋鹿玩偶").first
    await d.click(r.get_by_role("button", name="編輯"), after=1.0)
    await d.fill(M.get_by_label(re.compile("^價格")), "249", after=0.4)
    await d.fill(M.get_by_label(re.compile("^庫存")), "50", after=0.4)
    await d.click(M.get_by_role("button", name="儲存"), after=2.2)
    await d.highlight(P.locator("tr", has_text="聖誕麋鹿玩偶").first, sec=1.6)

    d.cap("刪除沒有被訂單引用的商品；被引用的只能下架", "Delete unused products; referenced ones can only be unlisted")
    r = P.locator("tr", has_text="聖誕麋鹿玩偶").first
    await d.click(r.get_by_role("button", name="刪除"), after=1.0)
    foot = M.locator(".bo-modal__foot")
    if await foot.count():
        await d.click(foot.get_by_role("button").last, after=2.2)
    else:
        await d.wait(2.0)
    d.end_cap()
