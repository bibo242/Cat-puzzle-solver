# Cat Sort Solver

A GUI tool to solve cat sort puzzles (like water sort but with cats).

## Setup

```bash
pip install flet
python gui.py
```

## Usage

1. **Get state** — click "Copy AI Prompt", take a screenshot of your game, paste both into an AI chat. It returns a JSON array. Or type it manually:
   ```json
   [["orange","blue","green"], ["red","yellow"], []]
   ```

2. **Apply** — paste the JSON into the text field, click "Apply State".

3. **Set capacity** — max cats per tube (default 8).

4. **Set tubes** — number of tubes (including empty ones).

5. **Solve** — click "Solve". Use arrow buttons to step through the solution.

6. **Copy solution** — click "Copy" to get moves like:
   ```
   Step 1: 0 -> 9
   Step 2: 0 -> 3
   ```

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
