select customer_sk from {{ ref('dim_customer') }} group by customer_sk having count(*) > 1
