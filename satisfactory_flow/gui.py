import json
import os
from typing import List, Dict
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt

from .models import Node

WORKSPACE_FILE = "workspace.json"

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Satisfactory Flow")
        self.nodes: List[Node] = []
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_workspace()

    def _create_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(toolbar, text="Add Node", command=self.add_node).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Edit Node", command=self.edit_node).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Delete Node", command=self.delete_node).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Show Graph", command=self.show_graph).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Save", command=self.save_workspace).pack(side=tk.LEFT)

        self.node_list = tk.Listbox(self)
        self.node_list.pack(fill=tk.BOTH, expand=True)

        self.bind("<Control-s>", lambda _e: self.save_workspace())

    def refresh_list(self) -> None:
        self.node_list.delete(0, tk.END)
        for node in self.nodes:
            self.node_list.insert(tk.END, f"{node.name} | Power {node.power_usage():.2f} MW")

    def add_node(self) -> None:
        dlg = NodeDialog(self)
        node = dlg.result
        if node:
            self.nodes.append(node)
            self.refresh_list()

    def edit_node(self) -> None:
        sel = self.node_list.curselection()
        if not sel:
            return
        idx = sel[0]
        node = self.nodes[idx]
        dlg = NodeDialog(self, node)
        new_node = dlg.result
        if new_node:
            self.nodes[idx] = new_node
            self.refresh_list()

    def delete_node(self) -> None:
        sel = self.node_list.curselection()
        if not sel:
            return
        idx = sel[0]
        del self.nodes[idx]
        self.refresh_list()

    def build_graph(self) -> nx.DiGraph:
        G = nx.DiGraph()
        for idx, node in enumerate(self.nodes):
            G.add_node(idx, label=node.name)
        for src_idx, src in enumerate(self.nodes):
            for item in src.outputs:
                for dst_idx, dst in enumerate(self.nodes):
                    if src_idx == dst_idx:
                        continue
                    if item in dst.inputs:
                        G.add_edge(src_idx, dst_idx, label=item)
        return G

    def show_graph(self) -> None:
        G = self.build_graph()
        pos = nx.spring_layout(G)
        plt.figure(figsize=(8, 6))
        nx.draw(G, pos, with_labels=True, labels=nx.get_node_attributes(G, "label"))
        edge_labels = nx.get_edge_attributes(G, "label")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels)
        plt.show()

    def save_workspace(self) -> None:
        data = [n.to_dict() for n in self.nodes]
        with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "Workspace saved")

    def load_workspace(self) -> None:
        if os.path.exists(WORKSPACE_FILE):
            with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.nodes = [Node.from_dict(d) for d in data]
            self.refresh_list()

    def on_close(self) -> None:
        self.save_workspace()
        self.destroy()

class NodeDialog(simpledialog.Dialog):
    def __init__(self, master: tk.Misc, node: Node | None = None):
        self.node = node
        super().__init__(master, title="Node")

    def body(self, frame: tk.Frame) -> tk.Entry:
        self.vars: Dict[str, tk.Widget] = {}
        ttk.Label(frame, text="Name").grid(row=0, column=0)
        self.vars['name'] = tk.Entry(frame)
        self.vars['name'].grid(row=0, column=1)

        ttk.Label(frame, text="Base Power").grid(row=1, column=0)
        self.vars['base_power'] = tk.Entry(frame)
        self.vars['base_power'].grid(row=1, column=1)

        ttk.Label(frame, text="Inputs (item:qty, comma separated per line)").grid(row=2, column=0)
        self.vars['inputs'] = tk.Text(frame, width=30, height=4)
        self.vars['inputs'].grid(row=2, column=1)

        ttk.Label(frame, text="Outputs (item:qty, comma separated per line)").grid(row=3, column=0)
        self.vars['outputs'] = tk.Text(frame, width=30, height=4)
        self.vars['outputs'].grid(row=3, column=1)

        ttk.Label(frame, text="Clock Speed %").grid(row=4, column=0)
        self.vars['clock'] = tk.Entry(frame)
        self.vars['clock'].grid(row=4, column=1)

        ttk.Label(frame, text="Power Shards").grid(row=5, column=0)
        self.vars['shards'] = tk.Entry(frame)
        self.vars['shards'].grid(row=5, column=1)

        ttk.Label(frame, text="Filled Slots").grid(row=6, column=0)
        self.vars['filled'] = tk.Entry(frame)
        self.vars['filled'].grid(row=6, column=1)

        ttk.Label(frame, text="Total Slots").grid(row=7, column=0)
        self.vars['total'] = tk.Entry(frame)
        self.vars['total'].grid(row=7, column=1)

        if self.node:
            self.vars['name'].insert(0, self.node.name)
            self.vars['base_power'].insert(0, str(self.node.base_power))
            self.vars['inputs'].insert('1.0', "\n".join(f"{k}:{v}" for k, v in self.node.inputs.items()))
            self.vars['outputs'].insert('1.0', "\n".join(f"{k}:{v}" for k, v in self.node.outputs.items()))
            self.vars['clock'].insert(0, str(self.node.clock))
            self.vars['shards'].insert(0, str(self.node.shards))
            self.vars['filled'].insert(0, str(self.node.filled_slots))
            self.vars['total'].insert(0, str(self.node.total_slots))
        else:
            self.vars['clock'].insert(0, "100.0")
            self.vars['shards'].insert(0, "0")
            self.vars['filled'].insert(0, "0")
            self.vars['total'].insert(0, "0")

        return self.vars['name']

    def validate(self) -> bool:
        try:
            shards = int(self.vars['shards'].get())
            base_power = float(self.vars['base_power'].get())
            clock = float(self.vars['clock'].get())
            max_clock = min(250.0, 100.0 + shards * 50.0)
            if clock < 0 or clock > max_clock:
                raise ValueError
        except ValueError:
            messagebox.showerror(
                "Error",
                f"Invalid numeric input or clock exceeds limit ({max_clock:.1f}%)",
            )
            return False
        return True

    def apply(self) -> None:
        def parse(text: str) -> Dict[str, float]:
            lines = text.strip().splitlines()
            result: Dict[str, float] = {}
            for line in lines:
                if not line.strip():
                    continue
                parts = line.split(',')
                for p in parts:
                    if ':' in p:
                        item, qty = p.split(':', 1)
                        try:
                            result[item.strip()] = float(qty)
                        except ValueError:
                            pass
            return result

        self.result = Node(
            name=self.vars['name'].get(),
            base_power=float(self.vars['base_power'].get()),
            inputs=parse(self.vars['inputs'].get('1.0', 'end')),
            outputs=parse(self.vars['outputs'].get('1.0', 'end')),
            clock=round(float(self.vars['clock'].get()), 4),
            shards=int(self.vars['shards'].get()),
            filled_slots=int(self.vars['filled'].get()),
            total_slots=int(self.vars['total'].get()),
        )


