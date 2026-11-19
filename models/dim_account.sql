select external_id as account_id, customer_id from {{ ref('identity_map') }} where source_name = 'api'
