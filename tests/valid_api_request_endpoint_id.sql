select f.* from {{ ref('fct_api_request') }} f
left join {{ ref('dim_endpoint') }} d on f.endpoint_id = d.endpoint_id
where d.endpoint_id is null
