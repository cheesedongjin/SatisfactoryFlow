# SatisfactoryFlow

This repository contains a simple Python GUI tool for calculating and visualizing resource flows in the game **Satisfactory**.  
The application allows you to create "nodes" representing production buildings or resource sources and computes power usage and production rates based on clock speed and power shards.

Features
--------
- Generate nodes automatically via **Auto Build**.
- Support for clock speeds from 0% to 250% with the Satisfactory overclocking power formula. The
  allowed maximum clock speed is automatically limited to `100% + 50% × shards` (capped at 250%).
- Clock speeds are stored with four decimal places of precision.
- Optional Somersloop style multiplier using filled and total slots that affects
  both production and power usage.
- Save and load a workspace automatically (`workspace.json`).
- Toggle unavailable alternate recipes via the **Recipes** button (saved in the workspace).
- Visualize node connections with a simple graph using NetworkX and Matplotlib.
- Workspace is automatically saved when using **Show Graph**.
- Shortcut **Ctrl+S** or the *Save* button to store the current workspace.

Run the tool with:
```bash
python3 satisfactory_flow_gui.py
```

If a graphical display cannot be detected the launcher will automatically
start a simple console interface instead.

### Requirements

Install the Python dependencies first:

```bash
pip install networkx matplotlib requests pydot pillow
```

You also need the Graphviz system package:

```bash
sudo apt-get install graphviz
```

Graphviz is used to draw the node graph without overlapping edges. If you want
to use the optional PyGraphviz bindings, see the [PyGraphviz installation
guide](https://pygraphviz.github.io/documentation/stable/install.html).

The GUI and models are now organized under the `satisfactory_flow` package.
`satisfactory_flow_gui.py` simply launches the app.

## Data files

The `data/` directory contains JSON files generated from the [Official Satisfactory Wiki](https://satisfactory.wiki.gg) templates. Only the fields relevant to this tool are kept and logistic supports are omitted:

- `items.json` – definitions for all items
- `buildings.json` – only manufacturing and extraction buildings with power usage, Somersloop slots, and `inputs`/`outputs` port counts
- `recipes.json` – all recipes including alternate recipes
- `belts_pipes.json` – conveyor belts and pipelines with throughput (no lifts or pumps)
- `power_plants.json` – buildings that generate power

Run `python3 scripts/update_data.py` to refresh these files from the wiki.

## Command line optimizer

`scripts/optimize_production.py` calculates the minimal number of buildings needed to reach a target production rate given limits on power shards and Somersloops. It prints a summary including the total power usage and can display a simple graph of the result.

Example:

```bash
PYTHONPATH=. python3 scripts/optimize_production.py 430 7 0 --base-power 20
```
