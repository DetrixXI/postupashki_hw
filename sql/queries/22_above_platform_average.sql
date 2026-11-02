-- 22. Стримеры с подписчиками выше среднего по своей площадке.
-- Строго больше среднего по всем стримерам площадки, сам стример в среднее входит;
-- platform_avg до 2 знаков; team — тег действующей команды, иначе NULL.
--
-- Колонки: streamer, platform, followers, platform_avg, team
-- Порядок: followers по убыванию, при равенстве streamer по возрастанию
-- Строк:   16

with temp as (
    select 
        s.nickname as streamer,
        pl.name as platform,
        s.followers as followers,
        round(avg(s.followers) over (partition by platform_id), 2) as platform_avg,
        t.tag as team
    from streamers s 
    left join platforms pl using(platform_id)
    left join team_members tm on tm.player_id = s.player_id and tm.left_at is NULL
    left join teams t using(team_id)
)
select * from temp
where followers > platform_avg
order by followers desc, streamer 
