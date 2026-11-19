select count(*) as exceptions from {{ ref('unresolved_events') }} having count(*) <> 30 or count(case when external_id = 'W-unmapped' then 1 end) <> 30
