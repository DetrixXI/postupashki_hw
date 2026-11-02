-- 15. Сколько донатов собрал каждый стример.
-- В ответе все стримеры: без донатов donations = 0 и total_amount = 0.00;
-- team — команда с left_at IS NULL, иначе пусто.
--
-- Колонки: streamer, platform, team, donations, total_amount
-- Порядок: total_amount по убыванию, при равенстве streamer по возрастанию
-- Строк:   40


with donat_stat as (
    select 
        count(st_don.donation_id) as donations,
        sum(st_don.amount) as total_amount,
        st.streamer_id as streamer_id
        from streams st
    left join stream_donations st_don using(stream_id)
    group by st.streamer_id
)
select 
    st.nickname as streamer,
    plt.name as platform,
    t.name as team,
    dt.donations as donations,
    dt.total_amount as total_amount
from streamers st
left join donat_stat dt using(streamer_id)
left join team_members tm on tm.player_id = st.player_id and tm.left_at is NULL
left join platforms plt using(platform_id)
left join teams t using(team_id)
order by total_amount desc, streamer


