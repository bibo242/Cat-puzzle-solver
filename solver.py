import heapq

def is_solved(state):
    for col in state:
        if len(col) == 0:
            continue
        if len(set(col)) != 1:
            return False
    return True

def heuristic(state):
    h = 0
    for col in state:
        if len(col) <= 1:
            continue
        blocks = 1
        for i in range(len(col) - 2, -1, -1):
            if col[i] != col[i + 1]:
                blocks += 1
        if blocks > 1:
            h += blocks - 1
    return h

def get_valid_moves(state, capacity):
    moves = []
    num_tubes = len(state)

    first_empty = None
    for i in range(num_tubes):
        if len(state[i]) == 0:
            first_empty = i
            break

    for src in range(num_tubes):
        if len(state[src]) == 0:
            continue
        top_color = state[src][-1]
        chunk_size = 0
        for item in reversed(state[src]):
            if item == top_color:
                chunk_size += 1
            else:
                break
        src_is_single_color = (chunk_size == len(state[src]))

        for dst in range(num_tubes):
            if src == dst:
                continue
            available = capacity - len(state[dst])
            if available == 0:
                continue

            if len(state[dst]) == 0:
                if dst != first_empty:
                    continue
                if src_is_single_color:
                    continue

            if len(state[dst]) > 0 and state[dst][-1] != top_color:
                continue

            move_count = min(chunk_size, available)
            moves.append((src, dst, move_count, top_color))

    return moves

def solve(initial_state, capacity=7):
    initial_tuple = tuple(tuple(col) for col in initial_state)
    if is_solved(initial_tuple):
        return []

    h0 = heuristic(initial_tuple)
    counter = 0
    open_set = [(h0, counter, 0, initial_tuple, [])]
    g_scores = {initial_tuple: 0}

    while open_set:
        f, _, g, state, path = heapq.heappop(open_set)

        if is_solved(state):
            return path

        for move in get_valid_moves(state, capacity):
            src, dst, move_count, color = move

            new_state = list(list(col) for col in state)
            for _ in range(move_count):
                new_state[src].pop()
                new_state[dst].append(color)
            new_tuple = tuple(tuple(col) for col in new_state)

            new_g = g + 1
            if new_tuple not in g_scores or new_g < g_scores[new_tuple]:
                g_scores[new_tuple] = new_g
                h = heuristic(new_tuple)
                counter += 1
                heapq.heappush(open_set, (new_g + h, counter, new_g, new_tuple, path + [move]))

    return None
