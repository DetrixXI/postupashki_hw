-- 23. Игроки, поигравшие больше чем за одну команду.
-- Считаются различные team_id по всем периодам, строго больше одного; current_team —
-- название команды с пустым left_at, current_team и streamer могут быть NULL.
--
-- Колонки: player, country, teams_count, current_team, streamer
-- Порядок: teams_count по убыванию, при равенстве player по возрастанию
-- Строк:   25

with player_stats as (
    select player_id, count(distinct team_id) as num
    from team_members 
    group by player_id
),
curr_team as (
    select player_id, team_id
    from team_members
    where left_at is null
),
num_of_teams (player_id, num, name) as (
    select
        ps.player_id,
        ps.num,
        t.name 
    from player_stats ps
    left join curr_team cr using(player_id)
    left join teams t using(team_id)
)
select 
    pl.nickname as player,
    pl.country as country,
    nt.num as teams_count,
    nt.name as current_team,
    st.nickname as streamer
from num_of_teams nt
left join streamers st using(player_id)
left join players pl using(player_id)
where nt.num > 1
order by teams_count desc, player

