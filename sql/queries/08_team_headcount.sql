-- 08. Сколько в команде игроков и сколько среди них стримеров.
-- Считаются только незакрытые периоды; команда без состава остаётся
-- в ответе с нулями, стримеры без player_id не учитываются.
--
-- Колонки: name, tag, players_now, streamers_now
-- Порядок: players_now по убыванию, при равенстве name по возрастанию
-- Строк:   24

select t.name, t.tag, count(tm.player_id) as players_now, count(s.streamer_id) as streamers_now from teams as t
left join team_members tm on tm.team_id = t.team_id and tm.left_at is NULL
left join streamers s on s.player_id = tm.player_id
GROUP BY t.name, t.tag
order by players_now desc, name
limit 24