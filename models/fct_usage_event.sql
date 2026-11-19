select event_id, cast(event_day as date) as event_date, customer_id, customer_sk, kind, external_id as workspace_id, user_id, session_id, feature_id, units
from {{ ref('int_resolved') }}
where kind = 'usage' and customer_sk is not null
