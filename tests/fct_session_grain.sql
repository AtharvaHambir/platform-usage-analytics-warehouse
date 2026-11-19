select session_id from {{ ref('fct_session') }} group by session_id having count(*) > 1
