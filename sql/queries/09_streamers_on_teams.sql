-- 09. Кто из стримеров за какую команду выступает сейчас.
-- Только действующие составы; стримеры без player_id не выводятся.
--
-- Колонки: streamer, platform, player, team, tag, followers
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   16

select s.nickname as streamer, p.name as platform, pl.nickname as player, t.name as team, t.tag as tag, s.followers from streamers as s
left join platforms p on p.platform_id = s.platform_id
left join players pl on pl.player_id = s.player_id
left join team_members tm on tm.player_id = pl.player_id and tm.left_at is NULL
left join teams t on t.team_id = tm.team_id
where t.team_id is not NULL
order by s.followers desc, streamer
limit 16



