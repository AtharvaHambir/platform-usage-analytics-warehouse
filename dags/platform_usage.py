"""Airflow 3 manual portfolio refresh. All tasks share the local project directory."""
from datetime import datetime, timedelta, timezone

from airflow.providers.standard.operators.bash import BashOperator
from airflow.sdk import DAG

with DAG(
    dag_id="platform_usage",
    start_date=datetime(2025, 11, 1, tzinfo=timezone.utc),
    schedule=None,
    catchup=False,
    max_active_runs=1,
    default_args={"retries": 1, "retry_delay": timedelta(seconds=5)},
) as dag:
    def step(task_id, args):
        return BashOperator(task_id=task_id, bash_command='cd "$PLATFORM_PROJECT" && "$PLATFORM_PYTHON" ' + args)

    generate = step("generate_sources", "generate.py")
    load = step("load_sources", "load.py api usage billing")
    build = step("build_and_test", "pipeline.py build")
    publish = step("publish_scorecard", "pipeline.py publish")
    generate >> load >> build >> publish
