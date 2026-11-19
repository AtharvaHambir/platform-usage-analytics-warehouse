select event_id from {{ ref('fct_usage_event') }} group by event_id having count(*) > 1
