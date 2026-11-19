with entries as (
    select event_date, customer_sk, currency, amount_cents from {{ ref('fct_invoice') }}
    union all
    select event_date, customer_sk, currency, amount_cents from {{ ref('fct_credit') }}
)
select event_date, customer_sk, currency, sum(amount_cents) as net_billed_cents
from entries group by event_date, customer_sk, currency
