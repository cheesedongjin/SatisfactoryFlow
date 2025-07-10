import json
import re
import requests

BASE_URL = 'https://satisfactory.wiki.gg/api.php'

TEMPLATES = {
    'items': 'Template:DocsItems.json',
    'buildings': 'Template:DocsBuildings.json',
    'recipes': 'Template:DocsRecipes.json',
}


def fetch_template(name: str) -> dict:
    params = {
        'action': 'parse',
        'page': TEMPLATES[name],
        'prop': 'wikitext',
        'format': 'json'
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    r.raise_for_status()
    data = r.json()
    wikitext = data['parse']['wikitext']['*']
    return json.loads(wikitext)


def save_json(data: dict, path: str) -> None:
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    items = fetch_template('items')
    buildings = fetch_template('buildings')
    recipes = fetch_template('recipes')

    # gather building usage from recipes to filter only production buildings
    produced_in: set[str] = set()
    variable_power: dict[str, dict[str, float]] = {}
    port_counts: dict[str, dict[str, int]] = {}
    for data in recipes.values():
        info = data[0]
        for b in info.get('producedIn', []):
            produced_in.add(b)
            min_p = info.get('minPower')
            max_p = info.get('maxPower')
            if min_p is not None or max_p is not None:
                vp = variable_power.setdefault(b, {"minPower": float("inf"), "maxPower": 0})
                if min_p is not None and min_p < vp["minPower"]:
                    vp["minPower"] = min_p
                if max_p is not None and max_p > vp["maxPower"]:
                    vp["maxPower"] = max_p
            cnt = port_counts.setdefault(b, {"inputs": 0, "outputs": 0})
            cnt["inputs"] = max(cnt["inputs"], len(info.get("ingredients", [])))
            cnt["outputs"] = max(cnt["outputs"], len(info.get("products", [])))

    # clean items: only keep basic fields
    clean_items = {}
    for k, v in items.items():
        info = v[0]
        clean_items[k] = {
            "name": info["name"],
            "stackSize": info.get("stackSize"),
            "energy": info.get("energy"),
            "form": info.get("form"),
        }
    save_json(clean_items, 'data/items.json')

    # helper to parse throughput from description
    def parse_throughput(desc: str) -> int | None:
        m = re.search(r"(?:up to|Capacity:)\s*([0-9]+)[^0-9]*(?:resources|m³).*per minute", desc)
        if m:
            return int(m.group(1))
        return None

    belts_pipes: dict[str, dict] = {}
    power_plants: dict[str, dict] = {}
    prod_buildings: dict[str, dict] = {}

    extra_production = {
        "Desc_MinerMk1_C", "Desc_MinerMk2_C", "Desc_MinerMk3_C",
        "Desc_WaterPump_C", "Desc_OilPump_C", "Desc_FrackingSmasher_C"
    }
    for cls, data in buildings.items():
        info = data[0]
        name = info["name"]

        # logistics buildings (only belts and pipelines)
        if any(key in cls for key in ["ConveyorBelt", "Pipeline"]):
            if any(s in cls for s in ["Lift", "Pump", "Junction", "Valve", "Support", "Wall", "Attachment", "Crossing", "Pole", "Stackable", "NoIndicator"]):
                continue
            entry = {"name": name}
            tp = parse_throughput(info.get("description", ""))
            if tp:
                entry["throughput"] = tp
            belts_pipes[cls] = entry
            continue

        # power plants
        if info.get("powerGenerated", 0) > 0:
            if info.get("isVehicle"):
                continue
            power_plants[cls] = {
                "name": name,
                "powerGenerated": info["powerGenerated"],
                "somersloopSlots": info.get("somersloopSlots", 0),
                "overclockable": info.get("overclockable", False),
                "burnsFuel": info.get("burnsFuel", []),
                "supplementPerMinute": info.get("supplementPerMinute", 0),
            }
            continue

        # production buildings
        if cls in produced_in or cls in extra_production:
            entry = {
                "name": name,
                "powerUsage": info.get("powerUsage", 0),
                "somersloopSlots": info.get("somersloopSlots", 0),
                "overclockable": info.get("overclockable", False),
                "inputs": port_counts.get(cls, {"inputs": 0})["inputs"],
                "outputs": port_counts.get(cls, {"outputs": 1})["outputs"],
            }
            if cls in variable_power:
                vp = variable_power[cls]
                entry["minPower"] = None if vp["minPower"] == float("inf") else vp["minPower"]
                entry["maxPower"] = vp["maxPower"]
            prod_buildings[cls] = entry

    # clean recipes: keep only needed fields
    clean_recipes = {}
    for cls, data in recipes.items():
        info = data[0]
        clean_recipes[cls] = {
            "name": info["name"],
            "duration": info["duration"],
            "ingredients": info.get("ingredients", []),
            "products": info.get("products", []),
            "producedIn": info.get("producedIn", []),
            "alternate": info.get("alternate", False),
            "minPower": info.get("minPower"),
            "maxPower": info.get("maxPower"),
        }

    save_json(clean_recipes, 'data/recipes.json')
    save_json(prod_buildings, 'data/buildings.json')
    save_json(belts_pipes, 'data/belts_pipes.json')
    save_json(power_plants, 'data/power_plants.json')


if __name__ == '__main__':
    main()
