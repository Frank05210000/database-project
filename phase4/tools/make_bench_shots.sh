#!/bin/bash
# Section 7 加索引前後比較：需要已匯入 sql_bench/bench_data.sql 的容器（預設 fuwa-bench）
cd "$(dirname "$0")/.." || exit 1
C=${1:-fuwa-bench}; S=tools/shot.sh
U=$(docker exec $C psql -U fuwa -d fuwa -Atc "SELECT min(user_id) + 100 FROM users WHERE loginid LIKE 'bench%'")
Q1="EXPLAIN (ANALYZE, COSTS OFF)
SELECT product_id, name, price FROM product
WHERE is_listed AND name ILIKE '%貓抓板%';"
Q2="EXPLAIN (ANALYZE, COSTS OFF)
SELECT order_id, order_time, status FROM orders
WHERE user_id = $U ORDER BY order_time DESC LIMIT 20;"
run() { for i in 1 2 3 4 5 6; do docker exec $C psql -U fuwa -d fuwa -Atc "$1" | sed -n 's/^Execution Time: //p'; done | tail -5 | sort -n | sed -n 3p; }
docker exec $C psql -U fuwa -d fuwa -qc "DROP INDEX IF EXISTS product_name_trgm, orders_user_time;" >/dev/null
echo "before: search $(run "$Q1")  orders $(run "$Q2")"
docker exec $C psql -U fuwa -d fuwa -c "$Q1" -c "$Q2" >/dev/null   # 先熱身快取
$S $C img/bench_before.png "${Q1%;};;$Q2"
docker exec $C psql -U fuwa -d fuwa -qc "CREATE EXTENSION IF NOT EXISTS pg_trgm;" >/dev/null
$S $C img/bench_index.png "CREATE INDEX product_name_trgm ON product USING gin (name gin_trgm_ops);;CREATE INDEX orders_user_time ON orders (user_id, order_time DESC);;ANALYZE product, orders;"
docker exec $C psql -U fuwa -d fuwa -c "$Q1" -c "$Q2" >/dev/null
$S $C img/bench_after.png "${Q1%;};;$Q2"
echo "after:  search $(run "$Q1")  orders $(run "$Q2")"
