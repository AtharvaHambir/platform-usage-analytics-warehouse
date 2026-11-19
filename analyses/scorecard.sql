-- Each output row has one metric, unit and value. Keep currencies separate.
select 'Operations' as team, 'API request attempts' as metric, 'requests' as unit, count(*) as value from fct_api_request
union all
select 'Operations', 'API success rate', 'percent', round(100.0 * avg(case when status between 200 and 299 then 1 else 0 end), 2) from fct_api_request
union all
select 'Product', 'Usage units from matched workspaces', 'units', sum(units) from fct_daily_usage
union all
select 'Product', 'Usage events awaiting identity mapping', 'events', count(*) from unresolved_events
union all
select 'Finance', 'Net billed including credits', currency, sum(net_billed_cents) / 100.0 from fct_daily_billing group by currency
order by team, metric, unit
