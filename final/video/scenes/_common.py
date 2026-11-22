"""Shared helpers for scenes. Demo accounts come from the app's seed data (db/init/03_seed.sql)."""
ACCOUNTS = {"alice": "customer123", "bob": "customer123", "staff": "staff123", "admin": "admin123", "manager": "staff123"}


async def login(page, base, user):
    """Log in through the API and store the JWT the way the frontend does (before recording)."""
    await page.goto(base + "/")
    status = await page.evaluate("""async ([u, p]) => {
        const r = await fetch('/api/auth/login', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                                  body: JSON.stringify({loginid: u, password: p})});
        const j = await r.json(); localStorage.setItem('fuwa_token', j.access_token || j.token); return r.status; }""",
                                 [user, ACCOUNTS[user]])
    assert status == 200, f"login {user} failed: {status}"


def row(page, text, sel="tr"):
    """The table row (or card) containing `text`."""
    return page.locator(sel, has_text=text).first
