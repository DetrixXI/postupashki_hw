-- 14. Средние убийства, смерти и помощь у ходовых героев.
-- Только герои с games >= 420; средние — round(avg(x), 2) по numeric, два знака.
--
-- Колонки: hero, games, avg_kills, avg_deaths, avg_assists
-- Порядок: avg_kills (округлённое) по убыванию, при равенстве hero по возрастанию
-- Строк:   29

select 
    h.name as hero,
    count(match_id) as games, 
    round(avg(kills), 2) as avg_kills,
    round(avg(deaths), 2) as avg_deaths,
    round(avg(assists), 2) as avg_assists
from match_players
left join heroes h using(hero_id)
group by hero_id, h.name
having count(match_id) >= 420
order by avg_kills desc, hero
