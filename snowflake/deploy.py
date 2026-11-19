"""Refresh the portfolio data, run dbt on Snowflake and verify the published metrics."""
import csv
import json
import os
import subprocess
import sys
from decimal import Decimal
from pathlib import Path

from check_connection import connect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from generate import FIELDS, SOURCES

NUMBERS = {"amount_cents", "units", "status", "latency_ms", "feature_id",
           "client_id", "endpoint_id", "user_id"}


def refresh(cur, source):
    path = ROOT / "data" / f"{source}.csv"
    with path.open(newline="") as stream:
        rows = csv.reader(stream)
        if next(rows) != FIELDS:
            raise ValueError(f"Unexpected header in {path.name}")
        expected = sum(1 for _ in rows)
    schema = ", ".join(f"{col} {'NUMBER' if col in NUMBERS else 'VARCHAR'}" for col in FIELDS)
    cur.execute(f"create or replace temporary table landing.incoming_{source} ({schema})")
    uri = path.as_uri().replace("'", "''")
    cur.execute(f"put '{uri}' @landing.upload overwrite=true")
    cur.execute(f"""copy into landing.incoming_{source} from @landing.upload
        files=('{source}.csv.gz') file_format=(type=csv skip_header=1
        field_optionally_enclosed_by='"' empty_field_as_null=true) on_error=abort_statement""")
    actual = cur.execute(f"select count(*) from landing.incoming_{source}").fetchone()[0]
    if actual != expected or not actual:
        raise ValueError(f"{source}: expected {expected} deliveries, found {actual}")
    cur.execute(f"create or replace table landing.{source} as select * from landing.incoming_{source}")
    print(f"Loaded {actual} {source} deliveries", flush=True)
    return actual


def main():
    evidence = ROOT / "evidence"
    with connect() as conn, conn.cursor() as cur:
        cur.execute("use warehouse PLATFORM_USAGE_XS")
        cur.execute("create temporary stage landing.upload")
        counts = {source: refresh(cur, source) for source in SOURCES}
    key = Path(os.environ["PLATFORM_SNOWFLAKE_KEY"]).expanduser()
    subprocess.run([str(Path(sys.executable).with_name("dbt")), "build", "--profiles-dir",
                    "snowflake", "--target-path", "target_snowflake"], cwd=ROOT, check=True,
                   env={**os.environ, "PLATFORM_SNOWFLAKE_KEY": str(key),
                        "DBT_SEND_ANONYMOUS_USAGE_STATS": "false"})
    results = json.loads((ROOT / "target_snowflake/run_results.json").read_text())["results"]
    with connect() as conn, conn.cursor() as cur:
        cur.execute("use warehouse PLATFORM_USAGE_XS")
        sql = (ROOT / "analyses/scorecard.sql").read_text().strip()
        actual = cur.execute(sql).fetchall()
        with (ROOT / "scorecard.csv").open() as f:
            expected = {(r["team"], r["metric"], r["unit"]): Decimal(r["value"]) for r in csv.DictReader(f)}
        if len(actual) != len(expected) or {(t,m,u): Decimal(str(v)) for t,m,u,v in actual} != expected:
            raise ValueError(f"Scorecard differs from local results: {actual}")
        cur.execute("create or replace view ANALYTICS.PLATFORM_SCORECARD as\n" + sql)
        published = cur.execute("select * from ANALYTICS.PLATFORM_SCORECARD order by team,metric,unit").fetchall()
        report = {"raw_deliveries": counts, "dbt_results": {r["unique_id"]: r["status"] for r in results},
                  "scorecard": published, "scorecard_query_id": cur.sfqid}
    (evidence / "snowflake_run.json").write_text(json.dumps(report, indent=2, default=str) + "\n")
    print("Verified and published ANALYTICS.PLATFORM_SCORECARD", flush=True)


if __name__ == "__main__":
    main()
