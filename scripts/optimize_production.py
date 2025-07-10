#!/usr/bin/env python3
"""Calculate optimal building plan for a given production target."""
from __future__ import annotations

import argparse
from satisfactory_flow.optimizer import (
    search_plan,
    visualize_plan,
    plan_power,
)


def main() -> None:
    parser = argparse.ArgumentParser(description="Production optimizer")
    parser.add_argument("target", type=float, help="Target production percentage (e.g. 430 for 430%)")
    parser.add_argument("shards", type=int, help="Maximum total power shards available")
    parser.add_argument("loops", type=int, help="Maximum total somersloops available")
    parser.add_argument("--base-power", type=float, default=1.0,
                        help="Base power usage per building (MW)")
    parser.add_argument("--no-graph", action="store_true", help="Do not display graph")
    args = parser.parse_args()

    target_factor = args.target / 100.0
    plan = search_plan(target_factor, args.shards, args.loops)
    print("Building plan:")
    for idx, p in enumerate(plan, 1):
        boost = p.production * 100 - 100
        print(f"Building {idx}: {p.clock:.1f}% clock, {p.shards} shards, {p.loops} loops -> {p.production*100:.1f}%")
    total = sum(p.production for p in plan) * 100
    print(f"Total production: {total:.1f}%")
    power = plan_power(plan, args.base_power)
    print(f"Total power usage: {power:.2f} MW")
    if not args.no_graph:
        visualize_plan(plan)


if __name__ == "__main__":
    main()
