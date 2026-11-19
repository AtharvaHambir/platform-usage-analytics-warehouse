select event_id, cast(event_day as date) as event_date, customer_id, customer_sk, kind, currency, amount_cents
from {{ ref('int_resolved') }}
where kind = 'payment' and customer_sk is not null
