select f.* from {{ ref('fct_usage_event') }} f
left join {{ ref('dim_workspace') }} d on f.workspace_id = d.workspace_id
where d.workspace_id is null
