-- 10. Все роли героев, которые умеют быть керри.
-- Только герои с ролью 'carry'; у каждого выводятся все его роли, по строке на роль.
--
-- Колонки: name, primary_attr, attack_type, role
-- Порядок: name по возрастанию, внутри героя role по возрастанию
-- Строк:   47

with correct_id (hero_id) as (
    select hero_id from hero_roles
    where role = 'carry'
)
select h.name, h.primary_attr, h.attack_type, hr.role from correct_id cid
left join heroes h on cid.hero_id = h.hero_id
right join hero_roles hr on hr.hero_id = cid.hero_id
order by h.name, hr.role
limit 47