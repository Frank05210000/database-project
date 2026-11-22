#!/bin/bash
# 建立 V1、V2 檢視表並擷取 Section 8 各查詢的執行結果（容器預設 fuwa-p4-db，已載入 sql/）
cd "$(dirname "$0")/.." || exit 1
C=${1:-fuwa-p4-db}; S=tools/shot.sh
for v in v1_store_daily_sales v2_product_sales; do
  name=$(grep -o 'CREATE VIEW [a-z_]*' sql_q/$v.sql | awk '{print $3}')
  docker exec -i $C psql -U fuwa -d fuwa -X -q -c "DROP VIEW IF EXISTS $name CASCADE;" >/dev/null
  # 只執行 CREATE VIEW 那一段（到第一個以分號結尾的行）
  awk '/^CREATE VIEW/{f=1} f{print} f&&/;$/{exit}' sql_q/$v.sql | docker exec -i $C psql -U fuwa -d fuwa -X -q -v ON_ERROR_STOP=1 || exit 1
done
# 檢視表 CREATE VIEW 敘述結束（第一個以分號結尾的行）之後的查詢
sel(){ awk 'done && NF{print} /^CREATE VIEW/{v=1} v && /;$/ && !done{done=1}' "$1"; }
$S $C img/q_v1.png "$(sel sql_q/v1_store_daily_sales.sql)"
$S $C img/q_v2.png "$(sel sql_q/v2_product_sales.sql)"
for q in q1_store_best_seller q2_top_customers q3_store_rating q4_discount_usage; do
  $S $C img/q_${q%%_*}.png "$(grep -v '^--' sql_q/$q.sql)"
done
