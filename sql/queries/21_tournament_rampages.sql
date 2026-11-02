-- 21. Турнирные выступления с KDA выше шестикратного среднего.
-- KDA = (kills + assists)::numeric / GREATEST(deaths, 1); порог — строго больше шести
-- средних KDA по всей match_players; только матчи турниров; kda округлить до 2 знаков.
--
-- Колонки: match_id, tournament, player, hero, kda
-- Порядок: kda по убыванию, при равенстве match_id, затем slot
-- Строк:   60

with tour_games as (
    select t.name, m.match_id from tournaments t
    left join matches m on m.tournament_id = t.tournament_id
),
avg_kda as (
    select
        avg(round(((mp.kills + mp.assists)::numeric / GREATEST(mp.deaths, 1)), 2)) as avg_kda
    from match_players mp
)
select 
    mp.match_id,
    tg.name as tournament, 
    pl.nickname as player, 
    h.name as hero, 
    round(((mp.kills + mp.assists) / GREATEST(mp.deaths, 1)), 2) as kda 
from match_players mp
join tour_games tg using(match_id)
left join players pl using(player_id)
left join heroes h using(hero_id)
where round(((mp.kills + mp.assists) / GREATEST(mp.deaths, 1)), 2) >
                                 6 * (select * from avg_kda limit 1)
order by kda desc, match_id

