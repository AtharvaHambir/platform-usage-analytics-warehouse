select event_id from {{ ref('fct_api_request') }} group by event_id having count(*) > 1
