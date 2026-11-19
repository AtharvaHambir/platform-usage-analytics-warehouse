select a.customer_sk from {{ ref('dim_customer') }} a join {{ ref('dim_customer') }} b
on a.customer_id=b.customer_id and a.valid_from < b.valid_from
where a.valid_to is null or b.valid_from < a.valid_to
