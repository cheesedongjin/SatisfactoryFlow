# SatisfactoryFlow

This repository contains a simple Python GUI tool for calculating and visualizing resource flows in the game **Satisfactory**.  
The application allows you to create "nodes" representing production buildings or resource sources and computes power usage and production rates based on clock speed and power shards.

Features
--------
- Add/edit/delete nodes with custom inputs, outputs and base power usage.
- Support for clock speeds from 0% to 250% with the Satisfactory overclocking power formula.
- Optional Somersloop style power multiplier using filled and total slot counts.
- Save and load a workspace automatically (`workspace.json`).
- Visualize node connections with a simple graph using NetworkX and Matplotlib.
- Shortcut **Ctrl+S** or the *Save* button to store the current workspace.

Run the tool with:
```bash
python3 satisfactory_flow_gui.py
```

## Data files

The `data/` directory contains JSON files generated from the [Official Satisfactory Wiki](https://satisfactory.wiki.gg) templates. Only the fields relevant to this tool are kept and logistic supports are omitted:

- `items.json` – definitions for all items
- `buildings.json` – only manufacturing and extraction buildings with power usage, Somersloop slots, and `inputs`/`outputs` port counts
- `recipes.json` – all recipes including alternate recipes
- `belts_pipes.json` – conveyor belts and pipelines with throughput (no lifts or pumps)
- `power_plants.json` – buildings that generate power

Run `python3 scripts/update_data.py` to refresh these files from the wiki.
