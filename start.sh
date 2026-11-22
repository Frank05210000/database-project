#!/bin/sh
# FUWA FUWA e-Shop：一個指令啟動 PostgreSQL、FastAPI 後端與 React 前端
#   ./start.sh          啟動（第一次會建置映像檔）
#   ./start.sh reset    清空資料庫後重新啟動（重新套用 db/init 的 schema、trigger、種子資料）
#   ./start.sh down     停止
set -e
cd "$(dirname "$0")"
case "$1" in
  down)  docker compose down; exit 0 ;;
  reset) docker compose down -v ;;
esac
docker compose up --build -d
echo ""
echo "等待後端就緒…"
for i in $(seq 1 60); do
  if curl -fs http://localhost:8001/api/health >/dev/null 2>&1; then break; fi
  sleep 2
done
echo ""
echo "  前端（顧客／工作人員／平台管理）  http://localhost:5173"
echo "  後端 API 文件                    http://localhost:8001/docs"
echo "  PostgreSQL                       localhost:5433  (fuwa / fuwa)"
echo ""
echo "  示範帳號：admin/admin123（平台管理員）、staff/staff123（工作人員）"
echo "            manager/staff123（工作人員＋管理員）、alice/customer123（顧客）"
echo ""
echo "  查看紀錄：docker compose logs -f    停止：./start.sh down"
