import json
import os
from typing import List, Dict, Set
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_pydot import to_pydot
from PIL import Image
import io

from .models import Node
from .auto import generate_workspace, set_disabled_recipes

WORKSPACE_FILE = "workspace.json"

class App(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Satisfactory Flow")
        self.nodes: List[Node] = []
        self.disabled_recipes: Set[str] = set()
        set_disabled_recipes(self.disabled_recipes)
        self._create_widgets()
        self.protocol("WM_DELETE_WINDOW", self.on_close)
        self.load_workspace()

    def _create_widgets(self) -> None:
        toolbar = ttk.Frame(self)
        toolbar.pack(side=tk.TOP, fill=tk.X)
        ttk.Button(toolbar, text="Show Graph", command=self.show_graph).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Save", command=self.save_workspace).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Auto Build", command=self.auto_build).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Recipes", command=self.manage_recipes).pack(side=tk.LEFT)

        self.node_list = tk.Listbox(self)
        self.node_list.pack(fill=tk.BOTH, expand=True)

        self.bind("<Control-s>", lambda _e: self.save_workspace())

    def refresh_list(self) -> None:
        self.node_list.delete(0, tk.END)
        for node in self.nodes:
            self.node_list.insert(tk.END, f"{node.name} | Power {node.power_usage():.2f} MW")


    def auto_build(self) -> None:
        dlg = AutoDialog(self)
        res = dlg.result
        if not res:
            return
        sources = set(res.get('sources', []))
        self.nodes = generate_workspace(res['item_id'], res['rate'], sources)
        self.refresh_list()

    def manage_recipes(self) -> None:
        dlg = RecipeDialog(self, self.disabled_recipes)
        res = dlg.result
        if res is not None:
            self.disabled_recipes = res
            set_disabled_recipes(self.disabled_recipes)

    def build_graph(self) -> nx.DiGraph:
        """Return a directed graph of all nodes with duplicates for ``count``."""
        G = nx.DiGraph()
        node_map: List[tuple[str, Node]] = []
        for idx, node in enumerate(self.nodes):
            cnt = max(1, int(round(node.count)))
            if node.name.startswith("Source"):
                cnt = 1
            for i in range(cnt):
                node_id = f"{idx}_{i}"
                if node.name.startswith("Source"):
                    label = node.name
                else:
                    label = f"{node.name}\n{node.clock:.1f}%"
                G.add_node(node_id, label=label)
                node_map.append((node_id, node))

        for src_id, src_node in node_map:
            for dst_id, dst_node in node_map:
                if src_id == dst_id:
                    continue
                for item in src_node.outputs:
                    if item in dst_node.inputs:
                        G.add_edge(src_id, dst_id, label=item)
        return G

    def show_graph(self) -> None:
        """Display the graph using Graphviz to avoid overlaps."""
        # Save workspace before showing the graph
        self.save_workspace()
        G = self.build_graph()

        # Convert to pydot graph and configure appearance
        P = to_pydot(G)
        P.set_rankdir("LR")
        for node in P.get_nodes():
            node.set_shape("rectangle")
            node.set_style("filled")
            node.set_fillcolor("#A7D3F3")

        # Render to PNG using Graphviz
        png_bytes = P.create_png(prog="dot")
        img = Image.open(io.BytesIO(png_bytes))

        fig, ax = plt.subplots(figsize=(img.width / 80, img.height / 80))
        ax.imshow(img)
        ax.axis("off")
        plt.tight_layout()
        plt.show()

    def save_workspace(self) -> None:
        data = {
            "nodes": [n.to_dict() for n in self.nodes],
            "disabled_recipes": list(self.disabled_recipes),
        }
        with open(WORKSPACE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        messagebox.showinfo("Saved", "Workspace saved")

    def load_workspace(self) -> None:
        if os.path.exists(WORKSPACE_FILE):
            with open(WORKSPACE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                self.nodes = [Node.from_dict(d) for d in data]
                self.disabled_recipes = set()
            else:
                self.nodes = [Node.from_dict(d) for d in data.get("nodes", [])]
                self.disabled_recipes = set(data.get("disabled_recipes", []))
            set_disabled_recipes(self.disabled_recipes)
            self.refresh_list()

    def on_close(self) -> None:
        self.save_workspace()
        self.destroy()

class AutoDialog(simpledialog.Dialog):
    def body(self, frame: tk.Frame) -> tk.Entry:
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'items.json'), 'r', encoding='utf-8') as f:
            self.items = json.load(f)
        names = sorted(v['name'] for v in self.items.values())
        self.name_map = {v['name']: k for k, v in self.items.items()}

        ttk.Label(frame, text='Target Item').grid(row=0, column=0)
        self.cb = ttk.Combobox(frame, values=names, state='readonly')
        self.cb.grid(row=0, column=1)
        if names:
            self.cb.set(names[0])

        ttk.Label(frame, text='Rate per minute').grid(row=1, column=0)
        self.rate = tk.Entry(frame)
        self.rate.grid(row=1, column=1)

        ttk.Label(frame, text='Max Somersloops').grid(row=2, column=0)
        self.somers = tk.Entry(frame)
        self.somers.grid(row=2, column=1)
        self.somers.insert(0, '0')

        ttk.Label(frame, text='Max Power Shards').grid(row=3, column=0)
        self.shards = tk.Entry(frame)
        self.shards.grid(row=3, column=1)
        self.shards.insert(0, '0')

        ttk.Label(frame, text='Source Items').grid(row=4, column=0, sticky='nw')
        self.source_frame = ttk.Frame(frame)
        self.source_frame.grid(row=4, column=1, sticky='w')
        self.source_boxes: List[ttk.Combobox] = []
        self._add_source_row()
        ttk.Button(frame, text='+', command=self._add_source_row).grid(row=5, column=1, sticky='w')

        return self.rate

    def validate(self) -> bool:
        try:
            float(self.rate.get())
            int(self.somers.get())
            int(self.shards.get())
        except ValueError:
            messagebox.showerror('Error', 'Invalid numeric input')
            return False
        return True

    def _add_source_row(self) -> None:
        row = ttk.Frame(self.source_frame)
        names = sorted(self.name_map.keys())
        cb = ttk.Combobox(row, values=names, state='readonly')
        if names:
            cb.set(names[0])
        cb.pack(side=tk.LEFT, fill=tk.X, expand=True)
        btn = ttk.Button(row, text='-', command=lambda r=row: self._remove_source_row(r))
        btn.pack(side=tk.LEFT)
        row.pack(fill=tk.X, pady=2)
        self.source_boxes.append((row, cb))

    def _remove_source_row(self, row: ttk.Frame) -> None:
        for i, (r, cb) in enumerate(self.source_boxes):
            if r == row:
                r.destroy()
                self.source_boxes.pop(i)
                break

    def apply(self) -> None:
        item_name = self.cb.get()
        item_id = self.name_map[item_name]
        rate = float(self.rate.get())
        loops = int(self.somers.get())
        shards = int(self.shards.get())
        source_ids = []
        for _row, cb in self.source_boxes:
            name = cb.get()
            if name in self.name_map:
                source_ids.append(self.name_map[name])
        self.result = {
            'item_id': item_id,
            'rate': rate,
            'max_loops': loops,
            'max_shards': shards,
            'sources': source_ids,
        }


class RecipeDialog(simpledialog.Dialog):
    def __init__(self, master: tk.Misc, disabled: Set[str]):
        self.disabled = set(disabled)
        with open(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'recipes.json'), 'r', encoding='utf-8') as f:
            self.recipes = json.load(f)
        super().__init__(master, title='Disabled Recipes')

    def body(self, frame: tk.Frame) -> tk.Entry:
        search_frame = ttk.Frame(frame)
        search_frame.pack(fill=tk.X, pady=2)
        ttk.Label(search_frame, text='Search').pack(side=tk.LEFT)
        self.search_var = tk.StringVar()
        entry = ttk.Entry(search_frame, textvariable=self.search_var)
        entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        canvas = tk.Canvas(frame, width=400, height=300)
        scrollbar = ttk.Scrollbar(frame, orient='vertical', command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        inner = ttk.Frame(canvas)
        canvas.create_window((0, 0), window=inner, anchor='nw')
        inner.bind('<Configure>', lambda e: canvas.configure(scrollregion=canvas.bbox('all')))

        self.vars: Dict[str, tk.BooleanVar] = {}
        self.checks: Dict[str, ttk.Checkbutton] = {}
        row = 0
        for r_id, rec in sorted(self.recipes.items(), key=lambda x: x[1]['name']):
            var = tk.BooleanVar(value=r_id in self.disabled)
            chk = ttk.Checkbutton(inner, text=rec['name'], variable=var)
            chk.grid(row=row, column=0, sticky='w')
            self.vars[r_id] = var
            self.checks[r_id] = chk
            row += 1

        self.search_var.trace_add('write', lambda *_: self._filter())
        self._filter()

        return entry

    def _filter(self) -> None:
        query = self.search_var.get().lower()
        for rid, chk in self.checks.items():
            name = self.recipes.get(rid, {}).get('name', '').lower()
            if query in name:
                chk.grid()
            else:
                chk.grid_remove()

    def apply(self) -> None:
        self.result = {rid for rid, var in self.vars.items() if var.get()}


