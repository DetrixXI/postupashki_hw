-- 12. Сборные предметы внутри сборных предметов.
-- Пары «предмет — непосредственный компонент», где компонент сам встречается
-- в item_recipe.item_id; каждая пара один раз, component_cost — цена штуки.
--
-- Колонки: item_name, component_name, quantity, component_cost
-- Порядок: item_name по возрастанию, внутри предмета component_name по возрастанию
-- Строк:   36

with comp_it as (
select item_id, component_id, quantity, i.name as name from item_recipe ir
left join items i using(item_id)
)
select DISTINCT
    ci.name as item_name, 
    ci_2.name as component_name,
    ci.quantity, 
    i.cost as component_cost 
from comp_it ci
left join comp_it ci_2 on ci_2.item_id = ci.component_id
left join items i on i.item_id = ci.component_id
where ci_2.name is not NULL
order by item_name, component_name
limit 36

