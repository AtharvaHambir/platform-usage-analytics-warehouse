select customer_sk, event_date, feature_id from {{ ref('fct_daily_usage') }} group by customer_sk, event_date, feature_id having count(*) > 1
