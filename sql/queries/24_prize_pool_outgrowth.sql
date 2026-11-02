-- 24. Турниры, чей призовой фонд больше суммы призовых всех предыдущих.
-- Предыдущие — со строго меньшим started_at, сравнение строгое; у первого турнира
-- prev_total и prev_count нули, не NULL; matches_played — число матчей турнира.
--
-- Колонки: tournament, started_at, prize_pool, prev_total, prev_count, matches_played
-- Порядок: started_at по возрастанию
-- Строк:   2

with match_counts as (
    select tournament_id,
    count(*) as matches_played
    from matches
    group by tournament_id
)
select 
    t.name as tournament,
    t.started_at,
    t.prize_pool,
    coalesce(p.prev_total, 0) as prev_total,
    coalesce(p.prev_count, 0) as prev_count,
    coalesce(mc.matches_played, 0) as matches_played
from tournaments t
left join match_counts mc using (tournament_id)
cross join lateral (
    select sum(x.prize_pool) as prev_total,
        count(*) as prev_count
    from tournaments x
    where x.started_at < t.started_at
) p
where t.prize_pool > coalesce(p.prev_total, 0)
order by t.started_at;