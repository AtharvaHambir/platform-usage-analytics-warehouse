select f.* from {{ ref('fct_api_request') }} f
left join {{ ref('dim_status') }} d on f.status = d.status
where d.status is null
