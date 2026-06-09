from collections import deque

def is_solved(state):
    """
    A state is solved if every tube is either:
    - Completely empty
    - Contains items of only ONE color, and all items of that color are in a single tube
    """
    seen_colors = set()
    for col in state:
        if len(col) == 0:
            continue
        if len(set(col)) != 1:
            return False
            
        color = col[0]
        if color in seen_colors:
            return False
        seen_colors.add(color)
    return True

def get_valid_moves(state, capacity):
    """
    Returns a list of valid moves in the form (source_idx, dest_idx, count, color).
    Rules:
    - Cannot move from an empty tube
    - Cannot move to a full tube
    - Move all contiguous same-colored cats from the top as a single group.
    - If there isn't enough space for all of them, move as many as will fit.
    """
    moves = []
    num_tubes = len(state)
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
        
        for dst in range(num_tubes):
            if src == dst:
                continue
                
            available_space = capacity - len(state[dst])
            if available_space == 0:
                continue
                
            # Valid if empty or top color matches
            if len(state[dst]) == 0 or state[dst][-1] == top_color:
                # We move as many matching cats as can fit.
                move_count = min(chunk_size, available_space)
                moves.append((src, dst, move_count, top_color))
                
    return moves

def solve(initial_state, capacity=7):
    """
    Performs Breadth-First Search (BFS) to find the shortest path of moves to solve the state.
    """
    initial_tuple = tuple(tuple(col) for col in initial_state)
    
    # State representation in queue: (current_state, path_of_moves_taken)
    queue = deque([ (initial_tuple, []) ])
    visited = set([initial_tuple])
    
    while queue:
        state, path = queue.popleft()
        
        if is_solved(state):
            return path
            
        for move in get_valid_moves(state, capacity):
            src, dst, move_count, color = move
            
            # Apply move
            new_state = list(list(col) for col in state)
            for _ in range(move_count):
                item = new_state[src].pop()
                new_state[dst].append(item)
            
            new_tuple = tuple(tuple(col) for col in new_state)
            
            if new_tuple not in visited:
                visited.add(new_tuple)
                queue.append((new_tuple, path + [move]))
                
    return None # No solution found
