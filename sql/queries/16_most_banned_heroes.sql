-- 16. Десятка самых банимых героев.
-- bans — строки match_bans, picks — строки match_players, bans_per_pick =
-- round(bans::numeric / picks, 2); первые десять берутся после сортировки.
--
-- Колонки: hero, bans, picks, bans_per_pick
-- Порядок: bans по убыванию, при равенстве hero по возрастанию
-- Строк:   10

with bans as (
    select count(match_id) as bans, hero_id from match_bans
    group by hero_id
),
picks as (
    select count(match_id) as picks, hero_id from match_players
    group by hero_id
)
select 
    hr.name as hero,
    bn.bans as bans,
    pc.picks as picks,
    round(bn.bans::numeric / pc.picks, 2) as bans_per_pick
from picks pc
left join bans bn using(hero_id)
left join heroes hr using(hero_id)
order by bans desc, hero
limit 10