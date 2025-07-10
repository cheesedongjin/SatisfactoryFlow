import json
import os
from typing import Dict, List

from .models import Node

WORKSPACE_FILE = "workspace.json"


def parse_lines(text: str) -> Dict[str, float]:
    result: Dict[str, float] = {}
    for line in text.strip().splitlines():
        if not line.strip():
            continue
        for part in line.split(','):
            if ':' in part:
                item, qty = part.split(':', 1)
                try:
                    result[item.strip()] = float(qty)
                except ValueError:
                    pass
    return result


class ConsoleApp:
    def __init__(self) -> None:
        self.nodes: List[Node] = []
        self.load_workspace()

    def load_workspace(self) -> None:
        if os.path.exists(WORKSPACE_FILE):
            with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.nodes = [Node.from_dict(d) for d in data]

    def save_workspace(self) -> None:
        data = [n.to_dict() for n in self.nodes]
        with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        print("Workspace saved")

    def list_nodes(self) -> None:
        if not self.nodes:
            print("No nodes defined")
            return
        for idx, node in enumerate(self.nodes):
            print(f"{idx}: {node.name} | Power {node.power_usage():.2f} MW")

    def add_node(self) -> None:
        name = input("Name: ").strip()
        base_power = float(input("Base Power: ").strip() or 0)
        print("Enter inputs (item:qty, comma separated per line). End with empty line")
        lines = []
        while True:
            ln = input()
            if not ln:
                break
            lines.append(ln)
        inputs = parse_lines("\n".join(lines))
        print("Enter outputs (item:qty, comma separated per line). End with empty line")
        lines = []
        while True:
            ln = input()
            if not ln:
                break
            lines.append(ln)
        outputs = parse_lines("\n".join(lines))
        shards = int(input("Power Shards (default 0): ").strip() or 0)
        max_clock = min(250.0, 100.0 + shards * 50.0)
        clock = float(input(f"Clock Speed % (0-{max_clock}): ").strip() or 100)
        if clock > max_clock:
            print(f"Clock speed limited to {max_clock}% due to shards")
            clock = max_clock
        clock = round(clock, 4)
        
        filled = int(input("Filled Slots (default 0): ").strip() or 0)
        total = int(input("Total Slots (default 0): ").strip() or 0)
        node = Node(name, base_power, inputs, outputs, clock, shards, filled, total)
        self.nodes.append(node)
        print("Node added")

    def delete_node(self) -> None:
        idx = int(input("Index to delete: "))
        if 0 <= idx < len(self.nodes):
            del self.nodes[idx]
            print("Node deleted")
        else:
            print("Invalid index")

    def run(self) -> None:
        print("Satisfactory Flow Console")
        while True:
            cmd = input("Command (help for list): ").strip().lower()
            if cmd in {"quit", "exit"}:
                self.save_workspace()
                break
            elif cmd == "help":
                print("Commands: list, add, delete, save, load, quit")
            elif cmd == "list":
                self.list_nodes()
            elif cmd == "add":
                self.add_node()
            elif cmd == "delete":
                self.delete_node()
            elif cmd == "save":
                self.save_workspace()
            elif cmd == "load":
                self.load_workspace()
                print("Workspace loaded")
            else:
                print("Unknown command")

