# AI Agent Testing Guide

This document describes how an automated agent can verify the basic
functionality of **SatisfactoryFlow**.

## Setup
1. Ensure Python 3.10 or newer is installed.
2. Install dependencies:
   ```bash
   pip install networkx matplotlib requests
   ```
3. (Optional) Run `python3 scripts/update_data.py` if you wish to refresh the
   data files from the Satisfactory wiki.

## Running the Application
Invoke the launcher script:
```bash
python3 satisfactory_flow_gui.py
```
- If a GUI display is available, a window will open.
- When no display is detected, the application automatically falls back to a
  console interface.

## Basic Manual Test Steps
1. **Auto Build**
   - Use the `Auto Build` button to generate nodes.
2. **Save Workspace**
   - Trigger the *Save* action (`Ctrl+S`, the GUI button or `save` command).
   - Verify that `workspace.json` is created or updated.
3. **Load Workspace**
   - Restart the application and check that previously created nodes are loaded.
4. **Build Graph** (GUI only)
   - Click *Show Graph*. The workspace should save automatically and a
     matplotlib window should display the node connections.

These steps provide a minimal smoke test for the application in both GUI and
console modes.
