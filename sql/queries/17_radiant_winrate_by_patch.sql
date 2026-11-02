-- 17. Доля побед светлой стороны по патчам.
-- Патч без единого матча не выводится; radiant_winrate — процент,
-- round(100.0 * radiant_wins / matches, 2).
--
-- Колонки: version, matches, radiant_wins, radiant_winrate
-- Порядок: radiant_winrate (округлённое) по убыванию, при равенстве version по возрастанию
-- Строк:   12

select 
    pt.version as version,
    count(match_id) as matches,
    sum(case when mt.winner = 'radiant' 
        then 
            1
        else 
            0 
        end) as radiant_wins,
    round(100.0 * sum(case when mt.winner = 'radiant' 
        then 
            1
        else 
            0 
        end) / count(match_id), 2) as radiant_winrate
from matches mt
left join patches pt using(patch_id)
group by version
order by radiant_winrate desc, version