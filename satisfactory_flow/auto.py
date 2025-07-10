import json
import os
from typing import Dict, List

from .models import Node

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

with open(os.path.join(DATA_DIR, 'items.json'), 'r', encoding='utf-8') as f:
    ITEMS: Dict[str, Dict] = json.load(f)
with open(os.path.join(DATA_DIR, 'recipes.json'), 'r', encoding='utf-8') as f:
    RECIPES: Dict[str, Dict] = json.load(f)
with open(os.path.join(DATA_DIR, 'buildings.json'), 'r', encoding='utf-8') as f:
    BUILDINGS: Dict[str, Dict] = json.load(f)


def _map_recipes() -> Dict[str, Dict]:
    mapping: Dict[str, Dict] = {}
    for data in RECIPES.values():
        for prod in data.get('products', []):
            item = prod['item']
            if item not in mapping or mapping[item].get('alternate'):
                if not data.get('alternate'):
                    mapping[item] = data
                elif item not in mapping:
                    mapping[item] = data
    return mapping


RECIPES_BY_OUTPUT = _map_recipes()


def _gen_nodes(item_id: str, rate: float, nodes: List[Node], seen: set[str] | None = None) -> None:
    if seen is None:
        seen = set()
    if item_id in seen:
        item_name = ITEMS.get(item_id, {}).get('name', item_id)
        nodes.append(Node(name=f"Loop {item_name}", base_power=0.0, inputs={}, outputs={item_name: rate}))
        return
    seen.add(item_id)
    recipe = RECIPES_BY_OUTPUT.get(item_id)
    item_name = ITEMS.get(item_id, {}).get('name', item_id)
    if not recipe:
        nodes.append(Node(name=f"Source {item_name}", base_power=0.0,
                          inputs={}, outputs={item_name: rate}))
        return

    building_id = recipe.get('producedIn', [None])[0]
    building = BUILDINGS.get(building_id, {
        'name': building_id or 'Manual',
        'powerUsage': 0,
        'somersloopSlots': 0,
    })

    building_name = building.get('name', building_id or 'Manual')
    base_power = building.get('powerUsage', 0.0)

    out_amount = 0.0
    for p in recipe.get('products', []):
        if p['item'] == item_id:
            out_amount = p['amount']
            break
    per_machine = out_amount * 60.0 / recipe['duration'] if recipe['duration'] else 0.0
    machines = rate / per_machine if per_machine > 0 else 1.0
    if machines < 1:
        machines = 1.0
    total_power = base_power * machines

    node = Node(
        name=f"{building_name} ({recipe['name']})",
        base_power=total_power,
        inputs={},
        outputs={item_name: rate},
    )
    nodes.append(node)

    for ing in recipe.get('ingredients', []):
        ing_id = ing['item']
        ing_rate = machines * ing['amount'] * 60.0 / recipe['duration']
        ing_name = ITEMS.get(ing_id, {}).get('name', ing_id)
        node.inputs[ing_name] = ing_rate
        _gen_nodes(ing_id, ing_rate, nodes, seen.copy())


def generate_workspace(item_id: str, rate: float) -> List[Node]:
    nodes: List[Node] = []
    _gen_nodes(item_id, rate, nodes, set())
    return nodes
