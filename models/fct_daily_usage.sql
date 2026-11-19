select customer_sk, event_date, feature_id, sum(units) as units, count(*) as events
from {{ ref('fct_usage_event') }}
group by customer_sk, event_date, feature_id
