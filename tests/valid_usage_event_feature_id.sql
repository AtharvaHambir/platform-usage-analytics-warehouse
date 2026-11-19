select f.* from {{ ref('fct_usage_event') }} f
left join {{ ref('dim_feature') }} d on f.feature_id = d.feature_id
where d.feature_id is null
