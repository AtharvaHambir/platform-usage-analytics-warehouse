select f.* from {{ ref('fct_api_request') }} f
left join {{ ref('dim_account') }} d on f.account_id = d.account_id
where d.account_id is null
