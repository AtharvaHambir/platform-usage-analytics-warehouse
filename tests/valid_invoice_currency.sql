select f.* from {{ ref('fct_invoice') }} f
left join {{ ref('dim_currency') }} d on f.currency = d.currency
where d.currency is null
