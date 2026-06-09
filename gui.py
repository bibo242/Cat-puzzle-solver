import copy
import json
import subprocess
import threading
import flet as ft
from solver import solve

COLOR_HEX = {
    "orange": "#FF8C00", "pink": "#FF69B4", "yellow": "#FFD700",
    "green": "#32CD32", "blue": "#4169E1", "purple": "#9B59B6",
    "red": "#E74C3C", "brown": "#8B4513", "white": "#ECF0F1",
    "black": "#2C3E50", "gray": "#95A5A6", "cyan": "#00CED1", "magenta": "#FF00FF",
    "empty": "#1E1E2E",
}

COLOR_EMOJI = {
    "orange": "🟠", "pink": "🩷", "yellow": "🟡", "green": "🟢",
    "blue": "🔵", "purple": "🟣", "red": "🔴", "brown": "🟤",
    "white": "⚪", "black": "⚫", "gray": "🩶", "cyan": "🔷", "magenta": "💜",
    "empty": "⬜",
}

COLOR_NAMES = list(COLOR_HEX.keys())

TUBE_W = 56
ITEM_H = 36
TUBE_BG = "#313244"
TUBE_BORDER = "#585B70"
EMPTY_BORDER = "#45475A"
TEXT_COLOR = "#CDD6F4"
ACCENT_GREEN = "#A6E3A1"
ACCENT_BLUE = "#89B4FA"


def main(page: ft.Page):
    page.title = "Cat Sort Solver"
    page.theme_mode = ft.ThemeMode.DARK
    page.window_width = 1200
    page.window_height = 800
    page.padding = 20
    page.bgcolor = "#1E1E2E"

    # State
    state = [[] for _ in range(5)]
    capacity = 8
    tubes_per_row = 6
    solution_moves = []
    current_step = 0
    initial_state = None

    # UI refs
    tubes_container = ft.Column(spacing=12, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
    status_label = ft.Text("Ready", size=13, color=TEXT_COLOR)
    step_label = ft.Text("No solution", size=15, weight=ft.FontWeight.BOLD, color=TEXT_COLOR)
    solution_md = ft.Text("", size=20, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER)
    solution_md_container = ft.Container(
        content=solution_md,
        padding=ft.padding.Padding.all(12),
        bgcolor="#181825", border_radius=12,
        border=ft.border.Border.all(width=1, color="#313244"),
        expand=True,
        alignment=ft.alignment.Alignment(0, 0),
    )
    back_btn = ft.Button("⏮", icon=ft.icons.Icons.ARROW_BACK, on_click=lambda e: step_back(), disabled=True)
    forward_btn = ft.Button("⏭", icon=ft.icons.Icons.ARROW_FORWARD, on_click=lambda e: step_fwd(), disabled=True)
    reset_btn = ft.Button("⟲", icon=ft.icons.Icons.REPLAY, on_click=lambda e: step_reset())
    solve_btn = ft.Button("✅ Solve", icon=ft.icons.Icons.PLAY_ARROW, on_click=lambda e: do_solve(), bgcolor="#43A047", color="white")
    capacity_dropdown = ft.Dropdown(label="Capacity", width=120, value="8", options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 13)], on_select=lambda e: set_capacity())
    tpr_dropdown = ft.Dropdown(label="Per row", width=100, value="6", options=[ft.dropdown.Option(key=str(i), text=str(i)) for i in range(1, 11)], on_select=lambda e: set_tubes_per_row())
    tube_count_input = ft.TextField(label="Tubes", width=80, value="5", text_align=ft.TextAlign.CENTER, keyboard_type=ft.KeyboardType.NUMBER)
    apply_tubes_btn = ft.Button("✓", width=40, on_click=lambda e: set_tube_count())
    color_dropdown = ft.Dropdown(label="Color", width=200, value="orange", options=[ft.dropdown.Option(key=c, text=f"{COLOR_EMOJI[c]} {c}") for c in COLOR_NAMES])
    state_text = ft.TextField(
        label="State (JSON arrays)", multiline=True, min_lines=4, max_lines=10,
        width=230, text_style=ft.TextStyle(size=12, color=TEXT_COLOR),
        bgcolor="#181825", border_color="#45475A",
    )

    def set_capacity():
        nonlocal capacity, state
        capacity = int(capacity_dropdown.value)
        for i in range(len(state)):
            if len(state[i]) > capacity:
                state[i] = state[i][:capacity]
        render_tubes()
        update_status()
        sync_state_text()

    def set_tubes_per_row():
        nonlocal tubes_per_row
        tubes_per_row = int(tpr_dropdown.value)
        render_tubes()

    def set_tube_count():
        nonlocal state
        try:
            n = int(tube_count_input.value)
        except ValueError:
            return
        n = max(1, min(20, n))
        tube_count_input.value = str(n)
        # Resize state array
        if n > len(state):
            state.extend([[] for _ in range(n - len(state))])
        elif n < len(state):
            state = state[:n]
        render_tubes()
        update_status()
        sync_state_text()

    def sync_state_text():
        state_text.value = json.dumps(state)

    def apply_state_text():
        nonlocal state
        try:
            parsed = json.loads(state_text.value)
            if not isinstance(parsed, list):
                raise ValueError("Expected a list of lists")
            state = [list(t) for t in parsed]
            tube_count_input.value = str(len(state))
            render_tubes()
            update_status()
        except Exception as ex:
            status_label.value = f"❌ Parse error: {ex}"
            status_label.update()

    def copy_prompt():
        prompt = (
            "Analyze this image and generate a JSON array describing the colors of the cats "
            "in the active tubes. Follow these specific formatting rules:\n\n"
            "1.  Structure: The output must be a JSON array of arrays, where each child array "
            "represents one active tube. Do not include locked tubes in the output.\n"
            "2.  Tube Order: Scan the unlocked/active tubes from left to right, top to bottom "
            "(processing the top row first, then the bottom row).\n"
            "3.  Cat Order & Capacity: For the cats inside each active tube, list their "
            "colors from bottom to top (starting from the bottom of the tube up to the "
            "top). The maximum capacity for cats inside each tube is 8.\n"
            "4.  Color Naming: Use simple, lowercase color terms such as \"green\", \"orange\", "
            "\"maroon\", \"red\", \"pink\", \"gray\", \"black\", \"purple\", \"yellow\", and \"brown\".\n"
            "5.  Color Distribution Constraint: There must be exactly 8 cats of each color "
            "across all active tubes in the entire image. Use this mathematical "
            "constraint to double-check and ensure your color classifications are "
            "perfectly balanced (i.e., every color you use must sum to exactly 8 across "
            "the entire JSON array).\n"
            "6.  Empty Tubes: If an active tube is empty, represent it as an empty array [].\n\n"
            "Provide only the final JSON array."
        )
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(input=prompt.encode())
            status_label.value = "✅ Prompt copied to clipboard"
        except FileNotFoundError:
            state_text.value = prompt
            status_label.value = "⚠️ xclip not found, prompt shown in text field"
        status_label.update()

    def on_slot_click(e):
        tube_idx, slot_idx = e.control.data
        tube = state[tube_idx]
        selected_color = color_dropdown.value

        if selected_color == "empty":
            if slot_idx < len(tube):
                tube.pop(slot_idx)
        elif slot_idx < len(tube):
            if tube[slot_idx] == selected_color:
                tube.pop(slot_idx)
            else:
                tube[slot_idx] = selected_color
        elif slot_idx >= len(tube):
            tube.append(selected_color)

        render_tubes()
        update_status()
        sync_state_text()

    def render_tubes():
        tubes_container.controls.clear()
        for row_start in range(0, len(state), tubes_per_row):
            row_end = min(row_start + tubes_per_row, len(state))
            row_controls = []
            for tube_idx in range(row_start, row_end):
                tube = state[tube_idx]
                n = len(tube)
                border_color = TUBE_BORDER
                if 0 < current_step <= len(solution_moves):
                    src, dst, _, _ = solution_moves[current_step - 1]
                    if tube_idx == src:
                        border_color = ACCENT_GREEN
                    elif tube_idx == dst:
                        border_color = ACCENT_BLUE

                # Build slots top-to-bottom so Column layout matches visual order
                slot_controls = []
                for slot_idx in range(capacity - 1, -1, -1):
                    if slot_idx < n:
                        color = tube[slot_idx]
                        bg = COLOR_HEX.get(color.lower(), "#888888")
                        slot = ft.Container(
                            width=TUBE_W - 10, height=ITEM_H - 6,
                            bgcolor=bg, border_radius=8,
                            border=ft.border.Border.all(width=1, color="rgba(0,0,0,0.25)"),
                            data=(tube_idx, slot_idx),
                            on_click=on_slot_click,
                            tooltip=color,
                        )
                    else:
                        slot = ft.Container(
                            width=TUBE_W - 10, height=ITEM_H - 6,
                            bgcolor="transparent", border_radius=8,
                            border=ft.border.Border.all(width=1.5, color=EMPTY_BORDER),
                            data=(tube_idx, slot_idx),
                            on_click=on_slot_click,
                        )
                    slot_controls.append(slot)

                tube_col = ft.Column(
                    controls=slot_controls,
                    spacing=2,
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                )
                tube_wrapper = ft.Container(
                    content=tube_col,
                    padding=ft.padding.Padding.all(6),
                    border=ft.border.Border.all(width=2, color=border_color),
                    border_radius=12,
                    bgcolor=TUBE_BG,
                    width=TUBE_W + 12,
                    height=capacity * (ITEM_H - 2) + 16,
                )
                tube_label = ft.Text(str(tube_idx), size=14, weight=ft.FontWeight.BOLD, color=TEXT_COLOR, text_align=ft.TextAlign.CENTER)
                row_controls.append(
                    ft.Column(controls=[tube_wrapper, tube_label], spacing=4, horizontal_alignment=ft.CrossAxisAlignment.CENTER)
                )

            tubes_container.controls.append(
                ft.Row(controls=row_controls, spacing=16, alignment=ft.MainAxisAlignment.CENTER)
            )
        page.update()

    def update_status():
        color_counts = {}
        for tube in state:
            for color in tube:
                color_counts[color] = color_counts.get(color, 0) + 1
        counts = list(color_counts.values())
        balanced = len(set(counts)) <= 1 if counts else True
        total = sum(len(t) for t in state)
        status_label.value = f"Tubes: {len(state)} | Cats: {total} | Colors: {len(color_counts)} | {'✅ Balanced' if balanced else '⚠️ Unbalanced'}"
        status_label.update()

    def do_solve():
        nonlocal solution_moves, current_step, initial_state
        if not any(state):
            status_label.value = "⚠️ Empty state"
            status_label.update()
            return

        solve_btn.disabled = True
        solve_btn.update()
        status_label.value = "🧮 Solving..."
        status_label.update()

        snapshot = copy.deepcopy(state)
        cap = capacity

        def run_solve():
            nonlocal solution_moves, current_step, initial_state
            try:
                moves = solve(snapshot, capacity=cap)
                if moves is None:
                    status_label.value = "❌ No solution"
                else:
                    solution_moves = moves
                    initial_state = snapshot
                    current_step = 0
                    status_label.value = f"✅ {len(moves)} moves"
                    update_step_ui()
                    render_tubes()
                    sync_state_text()
            except Exception as ex:
                status_label.value = f"❌ Error: {ex}"
            finally:
                solve_btn.disabled = False
                page.update()

        threading.Thread(target=run_solve, daemon=True).start()

    def step_fwd():
        nonlocal current_step
        if current_step < len(solution_moves):
            src, dst, count, color = solution_moves[current_step]
            for _ in range(count):
                state[dst].append(state[src].pop())
            current_step += 1
            update_step_ui()
            render_tubes()
            sync_state_text()

    def step_back():
        nonlocal current_step
        if current_step > 0:
            current_step -= 1
            src, dst, count, color = solution_moves[current_step]
            for _ in range(count):
                state[src].append(state[dst].pop())
            update_step_ui()
            render_tubes()
            sync_state_text()

    def step_reset():
        nonlocal state, current_step
        if initial_state is not None:
            state = copy.deepcopy(initial_state)
            current_step = 0
            update_step_ui()
            render_tubes()
            sync_state_text()

    def copy_solution():
        if not solution_moves:
            status_label.value = "⚠️ No solution to copy"
            status_label.update()
            return
        lines = []
        for i, (s, d, c, col) in enumerate(solution_moves, 1):
            lines.append(f"Step {i}: {s} -> {d}")
        text = "\n".join(lines)
        try:
            proc = subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE)
            proc.communicate(input=text.encode())
            status_label.value = "✅ Solution copied to clipboard"
        except FileNotFoundError:
            state_text.value = text
            status_label.value = "⚠️ xclip not found, solution shown in text field"
        status_label.update()

    def update_step_ui():
        if not solution_moves:
            step_label.value = "No solution"
            back_btn.disabled = True
            forward_btn.disabled = True
            solution_md.value = ""
        elif current_step == 0:
            step_label.value = f"0 / {len(solution_moves)}"
            back_btn.disabled = True
            forward_btn.disabled = False
            solution_md.value = "Initial state"
        elif current_step == len(solution_moves):
            step_label.value = f"{len(solution_moves)} / {len(solution_moves)}"
            back_btn.disabled = False
            forward_btn.disabled = True
            solution_md.value = f"✅ Solved!"
        else:
            src, dst, count, color = solution_moves[current_step - 1]
            step_label.value = f"{current_step} / {len(solution_moves)}"
            solution_md.value = f"Move {count} {color}\ntube {src} → tube {dst}"
            back_btn.disabled = False
            forward_btn.disabled = False

        step_label.update()
        back_btn.update()
        forward_btn.update()
        solution_md.update()

    def _build_md():
        pass

    def clear_all():
        nonlocal state, solution_moves, current_step, initial_state
        state = [[] for _ in range(len(state))]
        solution_moves = []
        current_step = 0
        initial_state = None
        update_step_ui()
        render_tubes()
        update_status()
        sync_state_text()

    # Build UI
    left = ft.Column(
        controls=[
            ft.Text("🐱 Cat Sort Solver", size=26, weight=ft.FontWeight.BOLD, color=TEXT_COLOR),
            ft.Divider(color="#45475A"),
            ft.Row([
                capacity_dropdown,
                tpr_dropdown,
                tube_count_input,
                apply_tubes_btn,
            ], spacing=8),
            ft.Divider(color="#45475A"),
            ft.Row([
                color_dropdown,
            ]),
            state_text,
            ft.Row([
                ft.Button("📋 Apply State", icon=ft.icons.Icons.CHECK, on_click=lambda e: apply_state_text(), bgcolor="#45475A", color="white"),
                ft.Button("📋 Copy AI Prompt", icon=ft.icons.Icons.COPY, on_click=lambda e: copy_prompt(), bgcolor="#45475A", color="white"),
            ], spacing=8),
            ft.Divider(color="#45475A"),
            solve_btn,
            ft.Button("🗑️ Clear All", icon=ft.icons.Icons.DELETE, on_click=lambda e: clear_all()),
            ft.Divider(color="#45475A"),
            status_label,
        ],
        spacing=8, width=360,
    )

    right = ft.Column(
        controls=[
            ft.Container(
                content=tubes_container,
                padding=ft.padding.Padding.all(16),
                bgcolor="#181825", border_radius=12,
                border=ft.border.Border.all(width=1, color="#313244"),
            ),
            ft.Row(
                controls=[back_btn, step_label, forward_btn, reset_btn, ft.Button("📋 Copy", on_click=lambda e: copy_solution(), bgcolor="#45475A", color="white")],
                alignment=ft.MainAxisAlignment.CENTER, spacing=12,
            ),
            solution_md_container,
        ],
        spacing=12, expand=True,
    )

    page.add(ft.Row(controls=[left, right], spacing=20, expand=True))
    render_tubes()
    update_step_ui()
    update_status()
    sync_state_text()


ft.run(main)
