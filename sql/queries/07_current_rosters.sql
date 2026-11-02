-- 07. Действующие составы: кто сейчас за кого играет.
-- Только незакрытые периоды (left_at IS NULL); игроки без команды не выводятся.
--
-- Колонки: nickname, country, mmr, team_name, joined_at
-- Порядок: joined_at по возрастанию, при равенстве nickname по возрастанию
-- Строк:   86

select p.nickname, country, mmr, t.name as team_name, joined_at from team_members
left join players p on p.player_id = team_members.player_id
left join teams t on t.team_id = team_members.team_id
where left_at is NULL
order by joined_at, nickname
limit 86



