-- 25. Место стримера-профессионала в рейтинге своей страны.
-- Только стримеры с player_id и действующей записью в team_members; место по mmr
-- по убыванию и country_players считаются по всей players; player — ник из players.
--
-- Колонки: player, country, mmr, country_rank, country_players, team_tag, platform
-- Порядок: country по возрастанию, внутри страны country_rank по возрастанию
-- Строк:   16

with ranked_players as (
    select p.player_id,
        p.nickname,
        p.country,
        p.mmr,
        rank() over (partition by p.country order by p.mmr desc) as country_rank,
        count(*) over (partition by p.country) as country_players
    from players p
)
select 
    rp.nickname as player,
    rp.country,
    rp.mmr,
    rp.country_rank,
    rp.country_players,
    t.tag as team_tag,
    pl.name as platform
from streamers s
join ranked_players rp using (player_id)
join team_members tm using (player_id)
join teams t using (team_id)
join platforms pl using (platform_id)
where tm.left_at is null
order by rp.country, rp.country_rank