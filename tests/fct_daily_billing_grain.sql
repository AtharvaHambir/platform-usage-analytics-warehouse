select customer_sk, event_date, currency from {{ ref('fct_daily_billing') }} group by customer_sk, event_date, currency having count(*) > 1
