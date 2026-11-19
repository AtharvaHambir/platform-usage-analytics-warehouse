select event_id from {{ ref('fct_usage_event') }} where units <= 0 or units is null
