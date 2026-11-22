#!/bin/sh
# 資料庫的 schema、trigger、種子與示範交易資料都在 db/init/*.sql，由 PostgreSQL 容器初次啟動時套用
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
