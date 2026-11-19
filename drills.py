"""Reproduce both failure cases in a temporary copy of the built project."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import duckdb

from generate import ROOT, SOURCES
from load import load


def compare_landing(test_db):
    with duckdb.connect(str(test_db)) as conn:
        reference = str(ROOT / "warehouse.duckdb").replace("'", "''")
        conn.execute(f"attach '{reference}' as baseline (read_only)")
        for name in SOURCES:
            left = f"select * from landing.{name}"
            right = f"select * from baseline.landing.{name}"
            for a, b in ((left, right), (right, left)):
                if conn.execute(f"({a}) except all ({b}) limit 1").fetchone():
                    raise RuntimeError(f"Retry changed the contents of {name}")


def run_drills():
    with tempfile.TemporaryDirectory() as folder:
        temp = Path(folder)
        db = temp / "retry.duckdb"
        # Model the state left by an interrupted multi-source task.
        load("api", db)
        with duckdb.connect(str(db)) as conn:
            partial = conn.execute("select count(*) from landing.api").fetchone()[0]
        for source in SOURCES:
            load(source, db)
        compare_landing(db)
        for subdir in ("models", "seeds", "tests"):
            shutil.copytree(ROOT / subdir, temp / subdir)
        for file in ("profiles.yml", "dbt_project.yml", "warehouse.duckdb", "scorecard.csv", "pipeline.py", "load.py", "generate.py"):
            shutil.copy(ROOT / file, temp / file)
        with duckdb.connect(str(temp / "warehouse.duckdb")) as conn:
            conn.execute("""update fct_daily_billing set net_billed_cents=net_billed_cents+100
                where (customer_sk, event_date, currency) in (select customer_sk,event_date,currency
                from fct_daily_billing order by event_date,customer_sk,currency limit 1)""")
        dbt_command = str(Path(sys.executable).with_name("dbt"))
        result = subprocess.run([dbt_command, "test", "--select", "source_billing_tieout", "--profiles-dir", "."], cwd=temp, capture_output=True)
        detail = json.loads((temp / "target/run_results.json").read_text())["results"][0]
        if not (result.returncode == 1 and detail["status"] == "fail" and detail["failures"] == 1):
            raise RuntimeError("Expected exactly one failing currency/day")
        before = (temp / "scorecard.csv").read_bytes()
        blocked = subprocess.run([sys.executable, "pipeline.py", "publish"], cwd=temp, capture_output=True)
        if b"Publication requires successful results" not in blocked.stderr or (temp / "scorecard.csv").read_bytes() != before:
            raise RuntimeError("Publication gate did not protect the scorecard")
        shutil.copytree(ROOT / "analyses", temp / "analyses")
        subprocess.run([sys.executable, "pipeline.py", "build"], cwd=temp, stdout=subprocess.DEVNULL, check=True)
        subprocess.run([sys.executable, "pipeline.py", "publish"], cwd=temp, check=True)
        assert before == (temp / "scorecard.csv").read_bytes()
        return {"rows_committed_before_simulated_interruption":partial, "replay_compared_to_clean_load":"all three raw tables equal including duplicates",
                "injected_error_cents":100, "failed_test":detail["unique_id"], "failed_currency_day_groups":detail["failures"],
                "publication_blocked":True, "full_rebuild_restored_identical_scorecard":True}


if __name__ == "__main__":
    print(json.dumps(run_drills(), indent=2))
