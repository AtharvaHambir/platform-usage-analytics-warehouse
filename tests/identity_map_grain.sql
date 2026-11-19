select source_name, external_id from {{ ref('identity_map') }} group by source_name, external_id having count(*) > 1
