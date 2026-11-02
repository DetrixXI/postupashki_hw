-- 29. Полное дерево сборки Guardian Greaves, Bloodthorn, Harpoon и Hurricane Pike.
-- Строка на каждый путь вниз, сам корень не выводится; lvl с 1, qty — quantity последнего
-- шага, qty_total — произведение quantity по пути, path — имена от корня через ' > '.
--
-- Колонки: root_item, lvl, component, qty, qty_total, path
-- Порядок: root_item по возрастанию, затем path по возрастанию
-- Строк:   34

with recursive tree as (
    select i.item_id as root_id,
           i.name as root_item,
           i.item_id,
           i.name as component,
           0 as lvl,
           null::integer as qty,
           1 as qty_total,
           i.name as path
    from items i
    where i.name in ('Guardian Greaves', 'Bloodthorn', 'Harpoon', 'Hurricane Pike')
    union all
    select t.root_id,
           t.root_item,
           r.component_id,
           ci.name,
           t.lvl + 1,
           r.quantity,
           t.qty_total * r.quantity,
           t.path || ' > ' || ci.name
    from tree t
    join item_recipe r using(item_id)
    join items ci on ci.item_id = r.component_id
)
select 
    root_item,
    lvl,
    component,
    qty,
    qty_total,
    path
from tree
where lvl > 0
order by root_item, path