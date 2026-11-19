select event_id from {{ ref('fct_credit') }} where amount_cents >= 0 or amount_cents is null
