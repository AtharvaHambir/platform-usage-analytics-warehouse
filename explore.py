"""Print the four read-only walkthrough queries against the included database."""
import duckdb
from generate import ROOT

with duckdb.connect(str(ROOT / "warehouse.duckdb"), read_only=True) as conn:
    for query in (ROOT / "walkthrough.sql").read_text().split(";"):
        if query.strip():
            print(query.strip().splitlines()[0])
            print(conn.sql(query))
