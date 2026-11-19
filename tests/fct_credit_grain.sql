select event_id from {{ ref('fct_credit') }} group by event_id having count(*) > 1
