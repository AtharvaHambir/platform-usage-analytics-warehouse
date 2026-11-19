select external_id as workspace_id, customer_id from {{ ref('identity_map') }} where source_name = 'usage'
