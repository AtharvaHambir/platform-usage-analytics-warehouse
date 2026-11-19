with all_rows as (
    select * from {{ source('landing', 'api') }} union all select * from {{ source('landing', 'usage') }} union all select * from {{ source('landing', 'billing') }}
), variants as (select distinct * exclude (delivery_id) from all_rows)
select event_id from variants group by event_id having count(*) > 1
