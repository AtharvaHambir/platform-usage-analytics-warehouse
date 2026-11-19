with atomic as (
    select event_date,customer_sk,feature_id,sum(units) as total from {{ ref('fct_usage_event') }} group by event_date,customer_sk,feature_id
)
select * from atomic full join {{ ref('fct_daily_usage') }} d using (event_date,customer_sk,feature_id)
where atomic.total is distinct from d.units
