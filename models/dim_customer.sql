select customer_id, plan_id, cast(effective_day as date) as valid_from,
       lead(cast(effective_day as date)) over (
           partition by customer_id order by effective_day
       ) as valid_to,
       cast(customer_id as varchar) || '/' || cast(effective_day as varchar) as customer_sk
from {{ ref('plan_changes') }}
