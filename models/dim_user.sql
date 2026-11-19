select distinct user_id, external_id as workspace_id from {{ ref('int_resolved') }} where kind = 'usage' and customer_sk is not null
