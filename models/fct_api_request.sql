select event_id, cast(event_day as date) as event_date, customer_id, customer_sk, kind, external_id as account_id, endpoint_id, client_id, status, latency_ms
from {{ ref('int_resolved') }}
where kind = 'api' and customer_sk is not null
