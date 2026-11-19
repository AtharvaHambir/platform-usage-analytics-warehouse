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

## Seven interview answers from this build

### 1. What does 250K mean?

| Source | Raw deliveries | Distinct source events | Accepted atomic facts |
|---|---:|---:|---:|
| API | 144,144 | 144,000 | 144,000 |
| Usage | 84,084 | 84,000 | 83,970 |
| Billing | 24,024 | 24,000 | 24,000 |
| **Combined** | **252,252** | **252,000** | **251,970** |

The number refers to raw deliveries across three files over the full 30 days, before deduplication. The generator delivers every thousandth event twice, starting with event zero. One usage event per day has an unmapped workspace. Those 30 distinct events remain available in unresolved_events. Counting session or daily facts again would count summaries of the same activity.

### 2. Why eight facts?

| Table | Grain and key | Business question |
|---|---|---|
| fct_api_request | One request attempt, event_id | Which endpoints have errors or slow responses? |
| fct_usage_event | One matched feature event, event_id | How many units of a feature were consumed? |
| fct_invoice | One issued invoice event, event_id | How much did we invoice? |
| fct_payment | One received payment event, event_id | How much cash was collected? |
| fct_credit | One issued credit, event_id | How much reduced the amount billed? |
| fct_session | One source-defined session, session_id | How many events and units occurred in a session? |
| fct_daily_usage | One customer version, date and feature | What was daily feature adoption? |
| fct_daily_billing | One customer version, date and currency with billing activity | How much did we bill after credits? |

The billing fixture uses one event per invoice, payment or credit. It does not model invoice lines or payment allocation. Net billed is invoices plus signed credits. Including payments would mix billing and collection. Before comparing usage and billing, aggregate each to a common customer and reporting period. Joining each event directly would multiply amounts.

### 3. Why twelve dimensions?

| Dimension | Key | Use |
|---|---|---|
| dim_customer | customer_sk per version, customer_id across versions | Attribute events to the right customer and historical plan |
| dim_account | account_id | Resolve the API account to its customer |
| dim_workspace | workspace_id | Resolve the product workspace to its customer |
| dim_user | user_id | Link a product user to a workspace |
| dim_date | event_date | Group dates by weekday |
| dim_plan | plan_id | Label the subscription tier |
| dim_feature | feature_id | Group usage by product feature |
| dim_endpoint | endpoint_id | Group requests by API route |
| dim_client | client_id | Compare browser, SDK and mobile traffic |
| dim_status | status | Label request outcomes |
| dim_event_type | kind | Explain event categories consistently |
| dim_currency | currency | Label and separate monetary units |

The fixture has one account, workspace, and billing ID per customer. The model keeps source keys distinct so the reporting joins are explicit. Lookup tables such as status are small teaching examples. An inline label could work at this scale.

### 4. What did SCD Type 2 preserve?

Only the customer's plan tier changes in this build. The source supplies effective dates. dim_customer orders the changes for each customer and uses LEAD to find the end of each version. An event matches when its day is on or after the start and strictly before the end, or the end is open. Of 200 customers, 100 upgrade on November 16, yielding 300 dimension rows. A November 15 event retains Basic. A November 16 event uses Pro. The SQL uses day precision, so intraday changes require a timestamp version of the model. A historical correction supplied in the change log is reapplied when the full refresh rebuilds the facts.

### 5. How did identity resolution work?

The project generates an authoritative mapping of 600 source IDs to 200 customers. For example, API A0, usage W0 and billing B0 map to customer 0. The join uses both source name and source ID. W-unmapped has no entry. Its 30 events are kept in unresolved_events and excluded from customer-level usage metrics. The scorecard reports that coverage gap. This is a deterministic lookup, and its correctness depends on the supplied crosswalk.

### 6. What did the quality checks catch?

The tests directory contains all 29 executable queries. evidence/run.json lists the individual results. Checks include event keys, fact grains, dimension relationships, historical overlap, one open customer version, usage quantity, credit sign, source-to-fact counts and grouped reconciliations. The fixture-specific check expects exactly 30 unresolved usage events. A production pipeline would use an agreed tolerance and track individual exceptions.

In a fault drill, drills.py added 100 cents to one customer/day/currency billing summary in a temporary database. Counts and keys still looked correct. The independent reconciliation rebuilt expected amounts from raw invoice and credit records and returned one failing date/currency group. The publisher rejected that test run. A complete rebuild restored the original scorecard. This was a deliberately injected defect.

### 7. What happens on a retry?

Each input is a complete immutable historical snapshot. The loader atomically replaces each source table, so rerunning one or all three sources yields the same raw rows. A drill committed only the API snapshot, replayed all three sources, and compared every row in both directions with a clean build, including duplicate multiplicities. All three matched. The monthly batch is small enough for a full refresh. A stream of partial daily files would need another loading strategy such as interval replacement or a keyed merge.

## Evidence and scope

The four tasks were executed locally using Airflow's DAG test command. The dbt build ran 9 seeds, 23 table models and 29 tests. The 23 models are 12 dimensions, 8 facts and 3 intermediate/exception tables. evidence/run.json records the task states, model counts and test results. evidence/drills.json records both drill outcomes. The simulated business metrics describe this generated dataset only.
