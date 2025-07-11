import json
import os
from typing import Dict, List, Set
from math import ceil

from .models import Node

DATA_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')

with open(os.path.join(DATA_DIR, 'items.json'), 'r', encoding='utf-8') as f:
    ITEMS: Dict[str, Dict] = json.load(f)
with open(os.path.join(DATA_DIR, 'recipes.json'), 'r', encoding='utf-8') as f:
    RECIPES: Dict[str, Dict] = json.load(f)
with open(os.path.join(DATA_DIR, 'buildings.json'), 'r', encoding='utf-8') as f:
    BUILDINGS: Dict[str, Dict] = json.load(f)

ITEMS_BY_NAME: Dict[str, str] = {v['name']: k for k, v in ITEMS.items()}
RECIPES_BY_NAME: Dict[str, Dict] = {v['name']: v for v in RECIPES.values()}


DISABLED_RECIPES: Set[str] = set()


def _map_recipes(disabled: Set[str] | None = None) -> Dict[str, Dict]:
    """Return best recipe choice for each item.

    Packaging and unpackaging recipes are ignored when a non-packaging recipe
    exists for the same item. If an item only has packaging related recipes,
    prefer the one that does not directly feed on the item itself. Otherwise the
    item is treated as a raw resource.
    """

    # Collect candidate recipes per item first
    by_item: Dict[str, List[Dict]] = {}
    for cls, data in RECIPES.items():
        if disabled and cls in disabled:
            continue
        if "Desc_Converter_C" in data.get("producedIn", []):
            continue
        for prod in data.get("products", []):
            by_item.setdefault(prod["item"], []).append(data)

    mapping: Dict[str, Dict] = {}

    def is_packaging(rec: Dict) -> bool:
        name = rec.get("name", "").lower()
        return name.startswith("packaged ") or name.startswith("unpackage")

    for item, recs in by_item.items():
        item_name = ITEMS.get(item, {}).get("name", "")
        non_pack = [r for r in recs if not is_packaging(r)]
        if non_pack:
            candidates = non_pack
        else:
            if item_name.lower().startswith("packaged "):
                pack_recs = [r for r in recs if r.get("name", "").lower().startswith("packaged ")]
                if not pack_recs:
                    continue
                candidates = pack_recs
            else:
                continue  # treat as raw resource

        # Prefer non-alternate recipes
        best = None
        for r in candidates:
            if not r.get("alternate"):
                best = r
                break
        if best is None:
            best = candidates[0]
        mapping[item] = best

    return mapping


RECIPES_BY_OUTPUT = _map_recipes()


def set_disabled_recipes(disabled: Set[str]) -> None:
    """Update globally disabled recipes and rebuild the recipe mapping."""
    global DISABLED_RECIPES, RECIPES_BY_OUTPUT
    DISABLED_RECIPES = set(disabled)
    RECIPES_BY_OUTPUT = _map_recipes(DISABLED_RECIPES)


def _gen_nodes(
    item_id: str,
    rate: float,
    nodes: List[Node],
    seen: set[str] | None = None,
    sources: Set[str] | None = None,
) -> None:
    if seen is None:
        seen = set()
    if sources and item_id in sources:
        item_name = ITEMS.get(item_id, {}).get("name", item_id)
        nodes.append(
            Node(
                name=f"Source {item_name}",
                base_power=0.0,
                inputs={},
                outputs={item_name: rate},
                primary_output=item_name,
            )
        )
        return
    if item_id in seen:
        item_name = ITEMS.get(item_id, {}).get('name', item_id)
        nodes.append(
            Node(
                name=f"Loop {item_name}",
                base_power=0.0,
                inputs={},
                outputs={item_name: rate},
                primary_output=item_name,
            )
        )
        return
    seen.add(item_id)
    recipe = RECIPES_BY_OUTPUT.get(item_id)
    item_name = ITEMS.get(item_id, {}).get('name', item_id)
    if not recipe:
        nodes.append(
            Node(
                name=f"Source {item_name}",
                base_power=0.0,
                inputs={},
                outputs={item_name: rate},
                primary_output=item_name,
            )
        )
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

    outputs: Dict[str, float] = {}
    for prod in recipe.get('products', []):
        prod_name = ITEMS.get(prod['item'], {}).get('name', prod['item'])
        prod_rate = machines * prod['amount'] * 60.0 / recipe['duration']
        outputs[prod_name] = prod_rate

    node = Node(
        name=f"{building_name} ({recipe['name']})",
        base_power=base_power,
        inputs={},
        outputs=outputs,
        count=machines,
        primary_output=item_name,
    )
    nodes.append(node)

    for ing in recipe.get('ingredients', []):
        ing_id = ing['item']
        ing_rate = machines * ing['amount'] * 60.0 / recipe['duration']
        ing_name = ITEMS.get(ing_id, {}).get('name', ing_id)
        node.inputs[ing_name] = ing_rate
        _gen_nodes(ing_id, ing_rate, nodes, seen.copy(), sources)


def generate_workspace(
    item_id: str, rate: float, sources: Set[str] | None = None
) -> List[Node]:
    nodes: List[Node] = []
    _gen_nodes(item_id, rate, nodes, set(), sources)
    nodes = _merge_nodes(nodes)
    return nodes


def _merge_nodes(nodes: List[Node]) -> List[Node]:
    merged: Dict[str, Node] = {}
    per_machine: Dict[str, float] = {}
    loops: Dict[str, float] = {}

    def recipe_rate(name: str, out_name: str) -> float:
        recipe_key = name.split("(")[-1].rstrip(")") if "(" in name else ""
        recipe = RECIPES_BY_NAME.get(recipe_key)
        if not recipe:
            return 0.0
        out_id = ITEMS_BY_NAME.get(out_name)
        amount = 0.0
        for p in recipe.get("products", []):
            if p["item"] == out_id:
                amount = p["amount"]
                break
        if amount <= 0:
            amount = recipe.get("products", [{}])[0].get("amount", 0)
        return amount * 60.0 / recipe.get("duration", 1)

    for node in nodes:
        key = node.name
        out_rate = node.outputs.get(node.primary_output, 0.0)
        if key.startswith("Loop "):
            loops[node.primary_output] = loops.get(node.primary_output, 0.0) + out_rate
            continue
        if key not in merged:
            merged[key] = Node(
                name=node.name,
                base_power=node.base_power,
                inputs=node.inputs.copy(),
                outputs=node.outputs.copy(),
                primary_output=node.primary_output,
                clock=100.0,
                shards=node.shards,
                filled_slots=node.filled_slots,
                total_slots=node.total_slots,
                count=0.0,
            )
            if key.startswith("Source"):
                per_machine[key] = out_rate / node.count if node.count else out_rate
            else:
                per_machine[key] = recipe_rate(node.name, node.primary_output)
        else:
            m = merged[key]
            for k, v in node.inputs.items():
                m.inputs[k] = m.inputs.get(k, 0.0) + v
            for k, v in node.outputs.items():
                m.outputs[k] = m.outputs.get(k, 0.0) + v

    # Merge loop outputs into corresponding nodes
    for item, rate in loops.items():
        target = None
        for node in merged.values():
            if node.primary_output == item and not node.name.startswith("Source"):
                target = node
                break
        if target:
            target.outputs[item] = target.outputs.get(item, 0.0) + rate
        else:
            key = f"Loop {item}"
            merged[key] = Node(
                name=key,
                base_power=0.0,
                inputs={},
                outputs={item: rate},
                primary_output=item,
            )

    result: List[Node] = []
    for key, node in merged.items():
        out_rate = node.outputs.get(node.primary_output, 0.0)
        pm = per_machine.get(key, 0.0)
        if key.startswith("Source"):
            # Keep a single source node regardless of the combined rate
            node.count = 1.0
            node.clock = 100.0
            result.append(node)
            continue
        if pm <= 0:
            # Source or loop; assume rate per machine equals first node rate
            pm = out_rate
            machines_needed = 1.0
        else:
            machines_needed = out_rate / pm
        int_count = max(1, ceil(machines_needed))
        clock = out_rate / (int_count * pm) * 100.0 if pm > 0 else 100.0
        if out_rate > 0 and pm > 0:
            scale = int_count / machines_needed if machines_needed > 0 else 1.0
            for k in node.inputs:
                node.inputs[k] *= scale
            for k in node.outputs:
                node.outputs[k] *= scale
        node.count = float(int_count)
        node.clock = round(clock, 4)
        result.append(node)

    return result
