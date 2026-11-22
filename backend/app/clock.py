"""統一使用台灣時間（部署在 Vercel 時伺服器是 UTC）。資料庫存的是不含時區的台灣當地時間。"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

TZ = ZoneInfo("Asia/Taipei")


def tw_now() -> datetime:
    return datetime.now(TZ).replace(tzinfo=None)


def tw_today() -> date:
    return tw_now().date()
