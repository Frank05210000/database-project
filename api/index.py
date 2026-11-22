"""Vercel Python 函式入口：把 /api/* 交給 backend/ 的 FastAPI 應用程式。"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "backend"))

from app.main import app  # noqa: E402,F401
