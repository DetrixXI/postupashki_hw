-- 26. Нарастающая сумма донатов внутри каждого стрима Вжлинка за 2021 год.
-- Стримы Вжлинка, начавшиеся в 2021 году по UTC, строка на каждый донат; running_total —
-- нарастающая сумма донатов своего стрима по sent_at_sec.
--
-- Колонки: stream_id, title, sent_at_sec, donor, amount, running_total
-- Порядок: stream_id по возрастанию, внутри стрима sent_at_sec по возрастанию
-- Строк:   192

select 
    s.stream_id,
    s.title,
    d.sent_at_sec,
    d.nickname as donor,
    d.amount,
    sum(d.amount) over (partition by s.stream_id order by d.sent_at_sec, d.donation_id rows between unbounded preceding and current row) as running_total
from streams s
join streamers st using (streamer_id)
join stream_donations d using (stream_id)
where st.nickname = 'Вжлинк'
  and s.started_at >= date '2021-01-01'
  and s.started_at < date '2022-01-01'
order by s.stream_id, d.sent_at_sec, d.donation_id