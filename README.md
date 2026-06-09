# Cat Sort Solver

A GUI tool to solve cat sort puzzles (like water sort but with cats).

## Setup

```bash
pip install flet
python gui.py
```

## Usage

1. **Enter state** — paste JSON arrays into the text field and click "Apply State", e.g.:
   ```json
   [["orange","blue","green"], ["red","yellow"], []]
   ```
   Or use the color dropdown + click slots to edit visually.

2. **Set capacity** — max cats per tube (default 8).

3. **Set tubes** — number of tubes (including empty ones).

4. **Solve** — click "Solve". Solution appears in the box below. Use arrow buttons to step through.

5. **Copy solution** — click "Copy" to get moves like:
   ```
   Step 1: 0 -> 9
   Step 2: 0 -> 3
   ```

6. **Copy AI Prompt** — copies a prompt to paste with a screenshot into an AI to extract tube state.

## How it works

**A\* search** finds the shortest sequence of moves to sort all cats into single-color tubes.

- **State** — each tube is a list of colors (bottom to top). Goal: every tube has exactly one color, each color in exactly one tube.
- **Heuristic** — counts how many color chunks exist across all tubes. If `red` appears in 3 separate chunks, that's 2 extra chunks needing at least 2 moves to merge. This guides A\* toward consolidation.
- **Move generation** — move a top color group from one tube to another if the destination is empty or has the same top color.
- **Pruning** — only move to the first empty tube (avoids exploring duplicate symmetric states), skip moves that place an already-sorted single-color tube onto empty.
- **Threading** — solver runs in a background thread so the UI stays responsive during search.

## Files

| File | Purpose |
|------|---------|
| `gui.py` | Flet desktop GUI — tube editor, solver controls, step playback |
| `solver.py` | A\* solver — `solve(state, capacity)` returns list of moves |
