-- 13. Сколько матчей сыграно в каждом году.
-- Год из started_at; tournament_matches — матчи с непустым tournament_id, ноль допустим.
--
-- Колонки: year, matches, tournament_matches
-- Порядок: year по возрастанию
-- Строк:   10

select 
    EXTRACT(YEAR FROM m.started_at) as year, 
    count(m.match_id) as matches,
    count(m.tournament_id) as tournament_matches 
    from matches m
GROUP BY EXTRACT(YEAR FROM m.started_at)
order by year
limit 10