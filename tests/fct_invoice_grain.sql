select event_id from {{ ref('fct_invoice') }} group by event_id having count(*) > 1
