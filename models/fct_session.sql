select session_id, user_id, workspace_id, customer_sk, min(event_date) as session_date,
       count(*) as event_count, sum(units) as units
from {{ ref('fct_usage_event') }}
group by session_id, user_id, workspace_id, customer_sk
