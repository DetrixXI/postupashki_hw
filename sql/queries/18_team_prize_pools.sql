-- 18. Призовые турниров, до которых добрались игроки команды.
-- Турнир в зачёт один раз, если игрок сыграл его матч в составе: joined_at <=
-- started_at::date < left_at (пустой left_at — сейчас); команды без турниров не выводятся.
--
-- Колонки: team, tag, tournaments, prize_total
-- Порядок: prize_total по убыванию, при равенстве team по возрастанию
-- Строк:   22

with team_tournaments as (
    select distinct
           tm.team_id,
           tr.tournament_id,
           tr.prize_pool
    from matches as m
    join tournaments tr on tr.tournament_id = m.tournament_id
    join match_players as mp on mp.match_id = m.match_id
    join team_members as tm on tm.player_id = mp.player_id
                                and tm.joined_at <= m.started_at::date
                                and (tm.left_at is null or m.started_at::date < tm.left_at)
)
select t.name as team,
       t.tag,
       count(*) as tournaments,
       sum(tt.prize_pool) as prize_total
from teams as t
join team_tournaments AS tt
  on tt.team_id = t.team_id
group by t.team_id, t.name, t.tag
order by prize_total desc, team