select f.* from {{ ref('fct_usage_event') }} f
left join {{ ref('dim_user') }} d on f.user_id = d.user_id
where d.user_id is null
