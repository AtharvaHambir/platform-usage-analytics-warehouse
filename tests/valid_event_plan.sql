select e.event_id from {{ ref('int_resolved') }} e where e.customer_id is not null and e.customer_sk is null
