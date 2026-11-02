-- 20. Герои, которых на патче банили чаще, чем брали.
-- Патч — matches.patch_id; в ответе пары с bans строго больше picks, diff = bans - picks.
--
-- Колонки: version, hero, bans, picks, diff
-- Порядок: diff по убыванию, затем hero по возрастанию, затем version по возрастанию
-- Строк:   99

with bans as (
    select pt.version as version, h.name as hero, count(mb.match_id) as bans from match_bans mb
    left join heroes h using(hero_id)
    left join matches m using(match_id)
    left join patches pt using(patch_id)
    group by h.name, pt.version

), 
picks as (
    select h.name as hero, pt.version as version, count(mp.match_id) as picks from match_players mp
    left join heroes h using(hero_id)
    left join matches m using(match_id)
    left join patches pt using(patch_id)
    group by h.name, pt.version
)
select b.version as version,
    b.hero as hero, 
    b.bans as bans, 
    p.picks as picks,
    b.bans - p.picks as diff 
from bans b 
join picks p using(hero, version)
where b.bans > p.picks
order by diff desc, hero, version
