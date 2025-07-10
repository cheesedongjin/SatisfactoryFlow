from __future__ import annotations

from dataclasses import dataclass
from typing import List
import networkx as nx
import matplotlib.pyplot as plt


@dataclass
class BuildingPlan:
    shards: int
    loops: int
    clock: float
    production: float


def building_power(clock: float, base_power: float, loops: int, slots: int = 4) -> float:
    """Return power usage for a single building with given settings."""
    return base_power * loops_multiplier(loops, slots) * ((clock / 100.0) ** 1.321928)


def plan_power(plan: List[BuildingPlan], base_power: float, slots: int = 4) -> float:
    """Total power usage of an entire building plan."""
    return sum(building_power(p.clock, base_power, p.loops, slots) for p in plan)


def loops_multiplier(loops: int, slots: int = 4) -> float:
    """Return production multiplier from somersloops."""
    if slots <= 0:
        return 1.0
    return (1 + loops / slots) ** 2


def max_clock_for_shards(shards: int) -> float:
    """Maximum clock speed allowed for given shard count."""
    return min(250.0, 100.0 + shards * 50.0)


def search_plan(target: float, max_shards: int, max_loops: int,
                slots: int = 4, max_shards_per_building: int = 3) -> List[BuildingPlan]:
    """Find a combination of buildings meeting the target production.

    The target is expressed as a multiple of base production (e.g. ``4.3`` for
    430%). Shards and loops are integers. Buildings may be partially
    underclocked to exactly hit the target.
    """
    best: tuple[int, int, int, List[BuildingPlan]] | None = None

    combos = []
    for s in range(0, max_shards_per_building + 1):
        for l in range(0, slots + 1):
            cap = max_clock_for_shards(s) / 100.0 * loops_multiplier(l, slots)
            combos.append((cap, s, l))
    combos.sort(reverse=True)

    def plan_key(p: List[BuildingPlan]) -> tuple[int, int, int]:
        return (len(p), sum(b.shards for b in p), sum(b.loops for b in p))

    def backtrack(remaining: float, shards_left: int, loops_left: int, plan: List[BuildingPlan]):
        nonlocal best
        if remaining <= 0:
            key = plan_key(plan)
            if best is None or key < best[:3]:
                best = (*key, list(plan))
            return
        if best is not None and len(plan) >= best[0]:
            return
        for cap, s, l in combos:
            if s <= shards_left and l <= loops_left:
                plan.append(BuildingPlan(shards=s, loops=l, clock=max_clock_for_shards(s), production=cap))
                backtrack(remaining - cap, shards_left - s, loops_left - l, plan)
                plan.pop()

    backtrack(target, max_shards, max_loops, [])
    if best is None:
        raise ValueError("Target cannot be met with given shards and loops")

    plan = best[3]
    # Adjust final building to hit the target exactly
    total = sum(p.production for p in plan)
    if total > target:
        diff = total - target
        last = plan[-1]
        new_prod = last.production - diff
        new_clock = (new_prod / loops_multiplier(last.loops, slots)) * 100.0
        plan[-1] = BuildingPlan(shards=last.shards, loops=last.loops,
                                clock=new_clock, production=new_prod)
    return plan


def visualize_plan(plan: List[BuildingPlan]) -> None:
    """Show a simple graph of the building plan."""
    G = nx.DiGraph()
    for i, p in enumerate(plan, 1):
        label = f"B{i}\nShards:{p.shards}\nLoops:{p.loops}\nClock:{p.clock:.1f}%"
        G.add_node(f"B{i}", label=label)
        G.add_edge(f"B{i}", "Output")
    G.add_node("Output", label="Total")
    pos = nx.spring_layout(G)
    nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, 'label'), node_color='lightblue')
    plt.show()

