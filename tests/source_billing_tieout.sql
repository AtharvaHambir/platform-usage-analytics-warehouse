with ledger as (
    select distinct event_id, event_day, currency, amount_cents from {{ source('landing', 'billing') }} where kind in ('invoice','credit')
), expected as (
    select cast(event_day as date) as event_date,currency,sum(amount_cents) as cents from ledger group by event_day,currency
), actual as (
    select event_date,currency,sum(net_billed_cents) as cents from {{ ref('fct_daily_billing') }} group by event_date,currency
)
select * from expected full join actual using (event_date,currency) where expected.cents is distinct from actual.cents
