-- 27. Пик онлайна против пика предыдущего эфира того же стримера.
-- Только площадка 'VK Play Live'; prev_peak — пик предыдущего по started_at эфира того
-- же стримера, delta — их разность; первый эфир каждого стримера не выводится.
--
-- Колонки: streamer, followers, started_at, title, peak_viewers, prev_peak, delta
-- Порядок: followers по убыванию, внутри стримера started_at по возрастанию
-- Строк:   592

with vk_streams as (
    select st.nickname as streamer,
        st.followers,
        s.started_at,
        s.title,
        s.peak_viewers,
        lag(s.peak_viewers) over (partition by s.streamer_id order by s.started_at) as prev_peak
    from streams s
    join streamers st using (streamer_id)
    join platforms pl using (platform_id)
    where pl.name = 'VK Play Live'
)
select 
    streamer,
    followers,
    started_at,
    title,
    peak_viewers,
    prev_peak,
    peak_viewers - prev_peak as delta
from vk_streams
where prev_peak is not null
order by followers desc, started_at