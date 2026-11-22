#!/usr/bin/env python3
"""Parse the implementation's 01_schema.sql into final/slides/schema_data.js for the
revised-schema slide (tables, columns, PK/FK, plus the Phase 3/4 changes).

    python3 final/slides/tools/schema_data.py [path/to/01_schema.sql]
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
SRC = Path(sys.argv[1]) if len(sys.argv) > 1 else \
    ROOT / ".claude/worktrees/eshop-implementation-b6539e/db/init/01_schema.sql"

# Changes since the midterm (Phase 2) schema — see the header comment of 01_schema.sql
REMOVED = {"orders": ["total"], "product_discount": ["discount_type", "start_date", "end_date"],
           "return_item": ["return_id"]}
ADDED = {"return_request": ["refund_total"], "store_staff": ["user_id", "store_id"]}
CHANGED = {"product_discount", "return_item", "orders", "return_request"}


def parse(sql):
    sql = re.sub(r"--[^\n]*", "", sql)
    tables = []
    for name, body in re.findall(r"CREATE TABLE (\w+) \((.*?)\n\);", sql, re.S):
        cols, pk, fks = [], set(), {}
        for line in [l.strip().rstrip(",") for l in body.split("\n") if l.strip()]:
            up = line.upper()
            if up.startswith("PRIMARY KEY"):
                pk |= {c.strip() for c in re.search(r"\((.*?)\)", line).group(1).split(",")}
            elif up.startswith("FOREIGN KEY"):
                m = re.search(r"FOREIGN KEY \((.*?)\)\s+REFERENCES (\w+)", line, re.I)
                for c in m.group(1).split(","):
                    fks.setdefault(c.strip(), m.group(2))
            elif up.startswith(("UNIQUE", "CHECK", "CONSTRAINT", "EXCLUDE")):
                continue
            else:
                m = re.match(r"(\w+)\s+", line)
                if not m:
                    continue
                c = m.group(1)
                cols.append(c)
                if "PRIMARY KEY" in up:
                    pk.add(c)
                r = re.search(r"REFERENCES (\w+)", line, re.I)
                if r:
                    fks[c] = r.group(1)
        out = [{"n": c, "pk": c in pk, "fk": fks.get(c), "new": c in ADDED.get(name, [])} for c in cols]
        out += [{"n": c, "removed": True} for c in REMOVED.get(name, [])]
        tables.append({"t": name, "changed": name in CHANGED, "cols": out})
    return tables


if __name__ == "__main__":
    data = parse(SRC.read_text())
    dst = ROOT / "final" / "slides" / "schema_data.js"
    dst.write_text("window.SCHEMA = " + json.dumps(data, ensure_ascii=False) + ";\n")
    for t in data:
        print(f"{t['t']:22s}", " ".join(("*" if c.get("pk") else "") + c["n"] + (f"→{c['fk']}" if c.get("fk") else "")
                                        + ("(+)" if c.get("new") else "") + ("(-)" if c.get("removed") else "")
                                        for c in t["cols"]))
