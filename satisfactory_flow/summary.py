from __future__ import annotations

from typing import Dict, List, Set

from .models import Node


def compute_summary(nodes: List[Node]) -> Dict[str, Dict[str, float] | float]:
    """Return overall resource balance and power usage.

    The result dictionary contains ``sources`` for required input items,
    ``byproducts`` for excess outputs not targeted, ``products`` for net
    production of targeted items and ``power`` for total power usage.
    """
    totals: Dict[str, float] = {}
    targets: Set[str] = {
        n.primary_output
        for n in nodes
        if n.primary_output and not n.name.startswith(("Source", "Loop"))
    }

    for n in nodes:
        for item, amt in n.scaled_outputs().items():
            totals[item] = totals.get(item, 0.0) + amt
        for item, amt in n.scaled_inputs().items():
            totals[item] = totals.get(item, 0.0) - amt

    sources: Dict[str, float] = {}
    byproducts: Dict[str, float] = {}
    products: Dict[str, float] = {}
    for item, val in totals.items():
        if val < -1e-6:
            sources[item] = -val
        elif val > 1e-6:
            if item in targets:
                products[item] = val
            else:
                byproducts[item] = val

    power = sum(n.power_usage() for n in nodes)
    return {
        "sources": sources,
        "byproducts": byproducts,
        "products": products,
        "power": power,
    }
