"""Run from any directory using the project environment."""
import argparse
import csv
import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

from generate import ROOT, SOURCES, generate
from load import load


def dbt(*args, check=True):
    executable = Path(sys.executable).with_name("dbt")
    return subprocess.run([str(executable), *args, "--profiles-dir", str(ROOT)], cwd=ROOT,
                          env={**os.environ, "DBT_SEND_ANONYMOUS_USAGE_STATS": "false"}, check=check)


def publish():
    # On the Airflow path this task is downstream of a successful build.
    checks = json.loads((ROOT / "target/run_results.json").read_text())
    required = {p.stem for p in (ROOT / "tests").glob("*.sql")}
    passed = {r["unique_id"].split(".")[-1] for r in checks["results"] if r["status"] == "pass"}
    if required != passed or any(r["status"] not in ("pass", "success") for r in checks["results"]):
        raise RuntimeError("Publication requires successful results for the complete check suite.")
    with duckdb.connect(str(ROOT / "warehouse.duckdb"), read_only=True) as conn:
        query = conn.execute((ROOT / "analyses/scorecard.sql").read_text())
        with tempfile.NamedTemporaryFile(mode="w", dir=ROOT, delete=False, newline="") as f:
            writer = csv.writer(f)
            writer.writerow([c[0] for c in query.description])
            writer.writerows(query.fetchall())
    os.replace(f.name, ROOT / "scorecard.csv")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["run", "build", "publish"], default="run", nargs="?")
    action = parser.parse_args().action
    if action == "run":
        generate()
        for source in SOURCES:
            load(source, ROOT / "warehouse.duckdb")
    if action in ("run", "build"):
        dbt("build")
    if action in ("run", "publish"):
        publish()
