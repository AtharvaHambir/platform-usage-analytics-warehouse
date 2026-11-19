select distinct cast(event_day as date) as event_date,
    {% if target.type == 'snowflake' %}
    dayofweekiso(cast(event_day as date))
    {% else %}
    extract(isodow from cast(event_day as date))
    {% endif %} as weekday_iso
from {{ ref('stg_events') }}
