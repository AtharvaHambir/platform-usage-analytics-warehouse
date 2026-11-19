# Platform Usage Analytics Warehouse

A reproducible portfolio project for a fictional software platform. Product tracks feature adoption, Operations tracks request health, and Finance tracks net billed amounts by currency. Running the pipeline generates synthetic CSV deliveries covering November 1–30, 2025, then creates the local warehouse and scorecard.

## Start with one customer

Run `python pipeline.py run`, then run `python explore.py` in the project environment. Customer 0 starts on Basic and upgrades to Pro on November 16. Compare requests on either side of that date. Then look at the two raw deliveries for request api-0, the one fact that survives, and the differences between raw, accepted, and quarantined rows. The generator creates these records on your machine.

## Reproduce the project

From the extracted project directory on macOS or Linux with Python 3.12, run:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python pipeline.py run
python explore.py
python drills.py
```

Package installation needs internet. After installation the data build runs locally. The main command regenerates the fixed sample and replaces this demo's landing tables, models, and published CSV. All currency amounts are stored as integer cents. The scorecard converts cents to currency units for display.

To reproduce the four-task Airflow run, from the same project directory:

```sh
export PLATFORM_PROJECT="$PWD"
export PLATFORM_PYTHON="$PWD/.venv/bin/python"
export AIRFLOW_HOME="$PWD/.airflow-home"
export AIRFLOW__CORE__LOAD_EXAMPLES=False
export AIRFLOW__CORE__DAGS_FOLDER="$PWD/dags"
python3.12 -m venv .airflow-env
.airflow-env/bin/pip install 'apache-airflow==3.1.3' --constraint https://raw.githubusercontent.com/apache/airflow/constraints-3.1.3/constraints-3.12.txt
.airflow-env/bin/airflow db migrate
.airflow-env/bin/airflow dags test platform_usage 2025-12-01
```

Airflow and dbt use separate Python environments so their dependencies can be installed independently. The DAG runs manually on one machine and permits one active run. The logical date identifies the run. The generator always produces the same 30-day historical fixture. This version performs a full refresh and publishes a CSV for its consumers.

## Architecture and ownership

| Stage | Code | What happens |
|---|---|---|
| Generate | generate.py | Produce three CSV snapshots, a trusted source-ID mapping and a dated log of plan changes. Each source supplies IDs and an event day. |
| Land | load.py | DuckDB reads typed CSV rows. Each complete source replaces its own landing table in one statement. If the second source fails, the first can already be committed. |
| Clean | models/stg_events.sql | Keep one delivery per source and event ID. The generated replays have identical business fields. A quality check detects conflicting payloads sharing an event ID. |
| Resolve identity | models/int_resolved.sql | Join on source plus external ID, then join the customer version valid on the event day. Left joins preserve unmatched records for inspection. |
| Build business tables | models/dim_*.sql and models/fct_*.sql | dbt builds models in dependency order. DuckDB executes the SQL. Separate facts preserve event grains and separate billing from cash collection. |
| Check | tests/ | dbt executes 29 named SQL assertions. Each selects violating rows. A successful full build is required before publishing the scorecard. |
| Publish | analyses/scorecard.sql and pipeline.py | Aggregate the curated facts and atomically replace the last scorecard with a completed CSV. The gate protects that file. Direct queries of warehouse tables can see models during a rebuild. |
| Coordinate | dags/platform_usage.py | Airflow runs generation, loading, dbt build and publication in order. A failed build prevents the dependent publication task from running. |

DuckDB runs the local demo in a single portable file. The Snowflake deployment uses the same source CSVs, seeds, models and tests. The local Airflow DAG targets DuckDB. The Snowflake refresh runs on demand from Python.

## Snowflake deployment

First run the local pipeline so the generated CSV files and comparison scorecard exist. Create a separate Python environment, install `snowflake/requirements.txt`, and copy `.env.example` to `.env`. Set `SNOWFLAKE_ACCOUNT` and `PLATFORM_SNOWFLAKE_KEY` to your own account and private-key path. In a POSIX shell, load those variables and deploy with:

```sh
set -a
. ./.env
set +a
python snowflake/deploy.py
```

A Snowflake refresh uses warehouse credits.

For a new Snowflake account, create an RSA key pair locally. Put only the base64 public key into `snowflake/01_grant_project_access.sql` where indicated, then run that worksheet once under a role allowed to create roles, a database, schemas, warehouse and user. Keep the private key in a local path excluded from Git.

The loader uploads the three CSVs to a temporary internal stage using PUT. It uses COPY INTO to populate a temporary table per source, checks the row count, then replaces the corresponding LANDING table. dbt builds the ANALYTICS schema. The publisher compares all six metrics with the local scorecard before creating the live view. A fresh clone will write its own local Snowflake run evidence.

In a Snowsight worksheet, a role with project access can run:

```sql
USE WAREHOUSE PLATFORM_USAGE_XS;
SELECT * FROM PLATFORM_USAGE_LAB.ANALYTICS.PLATFORM_SCORECARD
ORDER BY team, metric, unit;
```

## Project design

The warehouse combines three data domains that teams often analyze separately: API request activity, product feature usage, and billing events. It gives Product, Operations, and Finance a shared customer identity and consistent analytical tables for adoption, service health, invoices, payments, and credits.

The synthetic dataset covers November 1–30, 2025. It contains 252,252 raw deliveries representing 252,000 distinct source events. Each source includes a small number of duplicate deliveries to exercise deduplication. Thirty usage events use an unmapped workspace identifier and are retained in an exception model for visibility.

### Data model

The project contains eight fact tables for request attempts, usage events, invoices, payments, credits, sessions, daily usage, and daily billing. Each fact has an explicit grain so that metrics from different processes are not accidentally multiplied by joins. Twelve dimensions describe customers, accounts, workspaces, users, dates, plans, features, API endpoints, clients, statuses, event types, and currencies.

Customer identity is resolved through a source-specific crosswalk. The model joins using both source system and external identifier, then links events to the customer version valid on the event date. The customer dimension uses Type 2 history to retain plan changes over time. Unmatched events remain queryable in an exception model.

### Data quality and reliability

The dbt project includes 29 data tests for event uniqueness, fact grain, dimension relationships, valid values, historical ranges, source-to-model counts, and billing and usage reconciliations. A failure drill injects a billing discrepancy and demonstrates that reconciliation detects the error and blocks scorecard publication.

The local loader replaces each source landing table from a complete snapshot. Replaying a partial load produces the same landing data as a clean load, including duplicate deliveries. The Snowflake loader stages each CSV, copies it into a temporary table, checks row counts, then replaces the corresponding landing table.

### Results

| Metric | Result |
|---|---:|
| Raw deliveries processed | 252,252 |
| Distinct source events | 252,000 |
| API request attempts | 144,000 |
| API success rate | 97.87% |
| Unmapped usage events retained for review | 30 |
| dbt data tests passed | 29 |

The project runs locally with DuckDB and has also been deployed to Snowflake. Airflow orchestrates the local workflow. Python handles source loading to Snowflake and invokes the dbt build. The scorecard query reports monetary values by currency to avoid combining unlike units.

This is a portfolio implementation over deterministic synthetic data. Its counts and metrics describe the generated fixture.
