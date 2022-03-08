with accounts_w_domain as (
    -- just extract domain from email to be ref later
    -- also join subs. There is an implicit assumption one acc has at most one sub.
    -- this is checked in analysis
    -- seems to be OK for demo, however might not be the case on real data?
    select *, substr(email, instr(email, '@') + 1) as domain
    from accounts
             left join subscriptions s on accounts.account_id = s.account_id
),
     event_stats as (
         -- calculate required base statistics for events
         select account_id,
                count(*)                        n_events,
                sum(events.joined_participants) total_participants,
                sum(events.active_participants) total_active_participants,
                -- prolly can't be done due to grouping on domain
                -- avg(events.joined_participants) avg_participants,
                -- avg(events.active_participants) avg_active_participants,
                min(events.date)                first_event_date
         from events
         group by account_id
     ),
     stats_per_acc as (
         -- create final "base" table including stats and datediff required for activation
         select *, julianday(event_stats.first_event_date) - julianday(accounts_w_domain.date_signup) date_diff
         from accounts_w_domain
                  left join event_stats on accounts_w_domain.account_id = event_stats.account_id
     )
-- generate final export table
select domain,
       count(*)                       as              n_accounts,
       sum(users)                                     n_users,
       count(price)                                   n_paid_plans,
       sum(price)                                     revenue,
       sum(n_events)                                  n_events,
       sum(total_participants)                        total_participants,
       sum(total_active_participants) as              total_active_participants,
       sum(total_participants) / sum(n_events)        avg_participants,
       sum(total_active_participants) / sum(n_events) avg_active_participants,
       sum( case when date_diff <= 30 then 1 else 0 end)*1. / count(*)   activation_30,
       sum( case when date_diff <= 90 then 1 else 0 end)*1. /count(*)  activation_90
from stats_per_acc
group by domain;
