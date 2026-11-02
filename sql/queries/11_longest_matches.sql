-- 11. Самые затяжные матчи и турниры, на которых они сыграны.
-- duration_sec >= 4700 включительно; матчи вне турнира тоже выводятся, у них
-- tournament_name пуст; match_date — дата started_at по UTC.
--
-- Колонки: match_id, match_date, duration_sec, tournament_name
-- Порядок: duration_sec по убыванию, при равенстве match_id по возрастанию
-- Строк:   56

select m.match_id, m.started_at::date as match_date, m.duration_sec, t.name as tournament_name from matches m
left join tournaments t on m.tournament_id = t.tournament_id
where duration_sec >= 4700
order by m.duration_sec desc, match_id
limit 56