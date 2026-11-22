#!/bin/bash
# 用法：shot.sh <container> <out.png> <psql 指令（可含多行，以 ;; 分隔多個指令）>
# 把每個指令印成 fuwa=# 提示列＋psql 輸出，再畫成 PNG。
C=$1; OUT=$2; shift 2
TOOLS=$(cd "$(dirname "$0")" && pwd)
{
  IFS=$'\x1e'
  for cmd in $(printf '%s' "$*" | sed 's/;;/\x1e/g'); do
    first=1
    while IFS= read -r line; do
      if [ $first = 1 ]; then echo "fuwa=# $line"; first=0; else echo "fuwa-# $line"; fi
    done <<< "$cmd"
    printf '%s\n' "$cmd" | docker exec -i -e PAGER= -e COLUMNS=200 "$C" psql -U fuwa -d fuwa -X 2>&1
  done
} | sed -e 's/[[:space:]]*$//' | python3 -I "$TOOLS/term2png.py" "$OUT"
