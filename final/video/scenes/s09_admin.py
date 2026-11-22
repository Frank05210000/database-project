"""US-19 — platform admin: accounts, roles, deactivation."""
import pathlib, re, sys
sys.path.insert(0, str(pathlib.Path(__file__).parent))
from _common import login


async def setup(page, base):
    await login(page, base, "admin")


async def run(d):
    P = d.page
    M = P.locator(".bo-modal")
    await d.goto("/admin/users", wait=1.5)
    d.cap("平台管理員管理所有使用者帳號", "Admins manage every user account")
    await d.wait(1.5)

    d.cap("新增工作人員帳號並指派角色", "Create a staff account and assign roles")
    await d.click(P.get_by_role("button", name="＋ 新增使用者"), after=1.0)
    await d.type(M.get_by_label(re.compile("^登入帳號")), "demo_staff", delay=110)
    await d.type(M.get_by_label(re.compile("^姓名")), "林小芸", delay=120)
    await d.type(M.get_by_label(re.compile("^密碼")), "demo1234", delay=80)
    await d.type(M.get_by_label(re.compile("^Email")), "yun@fuwafuwa.tw", delay=50)
    await d.check(M.get_by_label("工作人員（staff）"))
    await d.click(M.get_by_role("button", name="建立帳號"), after=2.2)

    d.cap("一個使用者可以同時有多個角色", "One user can hold several roles")
    await d.click(P.locator("tr", has_text="demo_staff").first.get_by_role("button", name="角色"), after=1.0)
    await d.check(M.get_by_label(re.compile("^顧客")))
    await d.click(M.get_by_role("button", name="儲存角色"), after=2.2)

    d.cap("平台管理員也可以新增商店", "Admins can also open a new store")
    await d.goto("/admin/stores", wait=1.2)
    await d.click(P.get_by_role("button", name="＋ 新增商店"), after=1.0)
    await d.type(M.get_by_label(re.compile("^商店名稱")), "FUWA FUWA 台中店", delay=110)
    await d.type(M.get_by_label(re.compile("^地址")), "台中市西區公益路 100 號", delay=70)
    await d.type(M.get_by_label(re.compile("^Email")), "taichung@fuwafuwa.tw", delay=50)
    await d.type(M.get_by_label(re.compile("^電話")), "04-2300-0000", delay=60)
    await d.click(M.get_by_role("button", name="新增", exact=True), after=2.0)
    await d.highlight(P.locator("tr", has_text="FUWA FUWA 台中店").first, sec=1.8)
    await d.goto("/admin/users", wait=1.2)

    d.cap("停用違規的帳號", "Deactivate an account that broke the rules")
    await d.click(P.locator("tr", has_text="demo_dan").first.get_by_role("button", name="停用"), after=1.0)
    foot = M.locator(".bo-modal__foot")
    if await foot.count():
        await d.click(foot.get_by_role("button").last, after=2.0)
    await d.highlight(P.locator("tr", has_text="demo_dan").first, sec=1.8)

    d.cap("被停用的帳號無法登入", "A deactivated account can no longer log in")
    await d.click(P.get_by_role("button", name="登出"), after=1.2)
    await d.goto("/login", wait=0.8)
    await d.type(P.get_by_label("帳號", exact=True), "demo_dan", delay=110)
    await d.type(P.get_by_label("密碼", exact=True), "demo1234", delay=90)
    await d.click(P.get_by_role("button", name="登入", exact=True), after=3.0)
    d.end_cap()
