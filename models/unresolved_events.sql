select * from {{ ref('int_resolved') }} where customer_sk is null
