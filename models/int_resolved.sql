select e.*, m.customer_id, d.customer_sk
from {{ ref('stg_events') }} e
left join {{ ref('identity_map') }} m
  on e.source_name = m.source_name and e.external_id = m.external_id
left join {{ ref('dim_customer') }} d
  on d.customer_id = m.customer_id
 and cast(e.event_day as date) >= d.valid_from
 and (cast(e.event_day as date) < d.valid_to or d.valid_to is null)
