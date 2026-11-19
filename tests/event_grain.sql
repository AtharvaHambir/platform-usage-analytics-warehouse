select source_name, event_id from {{ ref('int_resolved') }} group by source_name, event_id having count(*) <> 1 or event_id is null
