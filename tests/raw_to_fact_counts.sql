with expected as (
    select kind,count(distinct event_id) as n from {{ source('landing', 'api') }} group by kind
    union all
    select kind,count(distinct event_id) as n from {{ source('landing', 'usage') }} group by kind
    union all
    select kind,count(distinct event_id) as n from {{ source('landing', 'billing') }} group by kind
), actual as (
    select kind, event_id from {{ ref('fct_api_request') }}
    union all
    select kind, event_id from {{ ref('fct_usage_event') }}
    union all
    select kind, event_id from {{ ref('fct_invoice') }}
    union all
    select kind, event_id from {{ ref('fct_payment') }}
    union all
    select kind, event_id from {{ ref('fct_credit') }}
    union all select kind,event_id from {{ ref('unresolved_events') }}
), counts as (select kind,count(*) as n from actual group by kind)
select * from expected full join counts using (kind) where expected.n is distinct from counts.n
