-- 19. Стримеры, которые ни разу не брали Pudge.
-- Только стримеры с непустым player_id и без единой игры за 'Pudge'; team — тег
-- команды с left_at IS NULL, иначе пусто; games — все строки match_players игрока.
--
-- Колонки: streamer, platform, team, followers, games
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   8

with pudge_id as (
    select hero_id from heroes
    where name = 'Pudge'
),
num_games as (
    select count(match_id) as games, pl.player_id as player_id from players pl
    left join match_players using(player_id)
    group by pl.player_id
),
streamers_no_pudge (streamer_id) as (
    select distinct st.streamer_id from streamers st
    where (select hero_id from pudge_id limit 1) not in (select hero_id from match_players where player_id = st.player_id)
    
)
select  
    s.nickname as streamer,
    plt.name as platform,
    t.tag as team,
    s.followers as followers,
    ng.games as games
from streamers_no_pudge snp
left join streamers s using(streamer_id)
left join team_members tm on tm.player_id = s.player_id and tm.left_at is NULL
left join num_games ng on ng.player_id = tm.player_id
left join platforms plt using(platform_id)
left join teams t using(team_id)
where t.tag is not null
order by s.followers desc, streamer

