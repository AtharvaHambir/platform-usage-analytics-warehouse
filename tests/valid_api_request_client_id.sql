select f.* from {{ ref('fct_api_request') }} f
left join {{ ref('dim_client') }} d on f.client_id = d.client_id
where d.client_id is null
