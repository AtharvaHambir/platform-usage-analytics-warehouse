with deliveries as (
    {% for source_name in ['api','usage','billing'] %}
    select '{{ source_name }}' as source_name, * from {{ source('landing', source_name) }}
    {% if not loop.last %} union all {% endif %}
    {% endfor %}
), ranked as (
    select *, row_number() over (
        partition by source_name, event_id order by delivery_id
    ) as delivery_rank
    from deliveries
)
select * exclude (delivery_rank) from ranked where delivery_rank = 1
