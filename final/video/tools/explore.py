#!/usr/bin/env python3
"""Dump the interactive elements of app pages (for writing scene selectors).

    python3 final/video/tools/explore.py ROLE PATH [PATH ...]      ROLE = guest|alice|staff|admin
Screenshots go to final/video/work/explore/.
"""
import asyncio
import re
import sys
from pathlib import Path

from playwright.async_api import async_playwright

BASE = "http://localhost:5173"
CREDS = {"alice": ("alice", "customer123"), "staff": ("staff", "staff123"),
         "admin": ("admin", "admin123"), "manager": ("manager", "staff123")}
OUT = Path(__file__).resolve().parents[1] / "work" / "explore"

DUMP = r"""() => {
  const vis = e => { const r = e.getBoundingClientRect(); return r.width > 0 && r.height > 0; };
  const t = e => (e.innerText || e.value || e.placeholder || e.getAttribute('aria-label') || e.title || '').trim().replace(/\s+/g, ' ').slice(0, 50);
  const out = [];
  document.querySelectorAll('h1,h2,h3,button,a[href],input,select,textarea,[role=tab],[role=button]').forEach(e => {
    if (!vis(e)) return;
    const tag = e.tagName.toLowerCase();
    let s = tag;
    if (tag === 'input' || tag === 'textarea' || tag === 'select') {
      s += `[${e.type || ''}] name=${e.name || ''} ph=${e.placeholder || ''}`;
      const lab = e.labels && e.labels[0] ? e.labels[0].innerText.trim() : '';
      if (lab) s += ` label=${lab.replace(/\s+/g, ' ').slice(0, 30)}`;
      if (tag === 'select') s += ' opts=' + [...e.options].map(o => o.value + ':' + o.text).slice(0, 8).join('|');
    } else if (tag === 'a') s += ` href=${e.getAttribute('href')} "${t(e)}"`;
    else s += ` "${t(e)}"` + (e.className && typeof e.className === 'string' ? ` .${e.className.split(' ')[0]}` : '');
    out.push(s);
  });
  return [...new Set(out)].join('\n');
}"""


async def main(role, paths):
    OUT.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch(channel="chrome")
        page = await b.new_page(viewport={"width": 1920, "height": 1080})
        await page.goto(BASE + "/")
        if role in CREDS:
            u, pw = CREDS[role]
            tok = await page.evaluate("""async ([u, p]) => { const r = await fetch('/api/auth/login', {method: 'POST',
                headers: {'Content-Type': 'application/json'}, body: JSON.stringify({loginid: u, password: p})});
                const j = await r.json(); const t = j.access_token || j.token; localStorage.setItem('fuwa_token', t); return r.status; }""", [u, pw])
            print("login", role, tok)
        for spec in paths:
            path, *clicks = spec.split(">")          # "/staff/products>＋ 新增商品" clicks text after loading
            await page.goto(BASE + path, wait_until="networkidle")
            await page.wait_for_timeout(600)
            for c in clicks:
                await page.get_by_text(c, exact=False).first.click()
                await page.wait_for_timeout(700)
            name = re.sub(r"\W+", "_", f"{role}{spec}").strip("_")
            await page.screenshot(path=str(OUT / f"{name}.png"), full_page=True)
            print(f"\n===== {role} {spec} → {page.url}")
            print(await page.evaluate(DUMP))
        await b.close()


if __name__ == "__main__":
    asyncio.run(main(sys.argv[1], sys.argv[2:]))
