select event_id from {{ ref('fct_payment') }} group by event_id having count(*) > 1
