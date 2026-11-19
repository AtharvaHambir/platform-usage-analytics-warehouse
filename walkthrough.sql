-- 1. Compare two deliveries of one API request.
select event_id, delivery_id, event_day, external_id from landing.api where event_id = 'api-0' order by delivery_id;

-- 2. Trace the surviving request through the account, customer and plan.
select f.event_id, f.account_id, a.customer_id, f.event_date, d.plan_id, d.valid_from, d.valid_to
from fct_api_request f join dim_account a using (account_id) join dim_customer d on f.customer_sk = d.customer_sk
where f.event_id in ('api-0','api-67200','api-72000') order by f.event_date;

-- 3. Inspect the exception queue.
select external_id, count(*) as unresolved_events, sum(units) as excluded_units from unresolved_events group by external_id;

-- 4. See the unit on each money total.
select currency, sum(net_billed_cents)/100.0 as net_billed from fct_daily_billing group by currency order by currency;
