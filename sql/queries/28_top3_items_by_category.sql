-- 28. Три самых дорогих предмета в каждой категории лавки.
-- Категория: 'recipe' при is_recipe, иначе 'assembled' при строках в item_recipe.item_id,
-- иначе 'basic'; place 1-3 по cost убыв., при равной цене по name; purchases — строк match_items, иначе 0.
--
-- Колонки: category, place, name, cost, purchases
-- Порядок: category по возрастанию, затем place по возрастанию
-- Строк:   9

with categorized as (
    select i.item_id,
            i.name,
            i.cost,
            case
            when i.is_recipe then 'recipe'
            when exists (select 1 from item_recipe r where r.item_id = i.item_id)
                then 'assembled'
                else 'basic'
            end as category
        from items i
),
purchases as (
    select item_id, count(*) as purchases
    from match_items
    group by item_id
),
ranked as (
    select c.category,
            c.name,
            c.cost,
            row_number() over (partition by c.category order by c.cost desc, c.name) as place,
            coalesce(p.purchases, 0) as purchases
    from categorized c
    left join purchases p using (item_id)
)
select 
    category,
    place,
    name,
    cost,
    purchases
from ranked
where place <= 3
order by category, place