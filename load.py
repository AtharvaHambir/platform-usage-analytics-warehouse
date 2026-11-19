"""Each source is replaced atomically from its complete immutable demo file."""
import argparse
from pathlib import Path

import duckdb

from generate import FIELDS, ROOT, SOURCES

INTS = {"amount_cents", "units", "status", "latency_ms", "feature_id", "client_id", "endpoint_id", "user_id"}


def load(source, db):
    with duckdb.connect(str(db)) as conn:
        conn.execute("create schema if not exists landing")
        types = {field: "INTEGER" if field in INTS else "VARCHAR" for field in FIELDS}
        csv_file = str(ROOT / "data" / f"{source}.csv")
        data = conn.read_csv(csv_file, header=True, columns=types)
        data.create_view("incoming")
        conn.execute(f"create or replace table landing.{source} as select * from incoming")


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("sources", nargs="+", choices=SOURCES)
    p.add_argument("--db", type=Path, default=ROOT / "warehouse.duckdb")
    args = p.parse_args()
    for source_name in args.sources:
        load(source_name, args.db)
