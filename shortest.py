from collections import deque
from math import inf

def _pawn_legal_targets_from_pos(env, player_idx, r, c, h_walls, v_walls):
    from Quoridor_Class import BOARD_SIZE
    opp = env.pawns[player_idx ^ 1]
    orr, occ = opp
    res = set()

    def can_cross(r1, c1, r2, c2):
        return not env._blocked_with(r1, c1, r2, c2, h_walls, v_walls)

    for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
        nr, nc = r + dr, c + dc
        if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
            continue
        if not can_cross(r, c, nr, nc):
            continue
        if (nr, nc) == (orr, occ):
            jr, jc = nr + dr, nc + dc
            if 0 <= jr < BOARD_SIZE and 0 <= jc < BOARD_SIZE and can_cross(nr, nc, jr, jc):
                if (jr, jc) != (r, c):
                    res.add((jr, jc))
            else:
                if dr != 0:
                    for dc2 in (-1, 1):
                        ar, ac = nr, nc + dc2
                        if 0 <= ac < BOARD_SIZE and can_cross(nr, nc, ar, ac):
                            res.add((ar, ac))
                else:
                    for dr2 in (-1, 1):
                        ar, ac = nr + dr2, nc
                        if 0 <= ar < BOARD_SIZE and can_cross(nr, nc, ar, ac):
                            res.add((ar, ac))
        else:
            res.add((nr, nc))
    res.discard((orr, occ))
    return res


def find_all_paths_to_goal(env, player_idx, max_paths=10, max_length_tolerance=2):
    from Quoridor_Class import BOARD_SIZE, ACTION_H_BASE
    
    start = env.pawns[player_idx]
    target_row = 0 if player_idx == 0 else BOARD_SIZE - 1
    
    if start[0] == target_row:
        return []
    
    q1 = deque([(*start, 0)])
    seen1 = {start}
    shortest_length = inf
    
    while q1:
        r, c, d = q1.popleft()
        if r == target_row:
            shortest_length = d
            break
        for nr, nc in _pawn_legal_targets_from_pos(env, player_idx, r, c, env.walls_h, env.walls_v):
            if (nr, nc) not in seen1:
                seen1.add((nr, nc))
                q1.append((nr, nc, d + 1))
    
    if shortest_length == inf:
        return []
    
    max_length = shortest_length + max_length_tolerance
    q2 = deque([(*start, 0, [start])])
    seen2 = set()
    paths_by_first_move = {}
    
    while q2:
        r, c, d, path = q2.popleft()
        
        if d > max_length:
            continue
        
        if r == target_row:
            if len(path) >= 2:
                first_pos = path[1]
                first_action = first_pos[0] * BOARD_SIZE + first_pos[1]
                if first_action < ACTION_H_BASE:
                    if first_action not in paths_by_first_move or d < paths_by_first_move[first_action][0]:
                        paths_by_first_move[first_action] = (d, first_action, path)
            continue
        
        for nr, nc in _pawn_legal_targets_from_pos(env, player_idx, r, c, env.walls_h, env.walls_v):
            state_key = (nr, nc, d + 1)
            if state_key not in seen2:
                seen2.add(state_key)
                q2.append((nr, nc, d + 1, path + [(nr, nc)]))
    
    paths_found = list(paths_by_first_move.values())
    paths_found.sort(key=lambda x: x[0])
    return paths_found[:max_paths]


def next_move_on_shortest_path(env, player_idx):
    paths = find_all_paths_to_goal(env, player_idx, max_paths=1)
    if paths:
        return paths[0][1]
    return None


def shortest_path_len(env, player_idx, h_walls=None, v_walls=None):
    from .Quoridor_Class import BOARD_SIZE
    h = env.walls_h if h_walls is None else h_walls
    v = env.walls_v if v_walls is None else v_walls
    start = env.pawns[player_idx]
    target_row = 0 if player_idx == 0 else BOARD_SIZE - 1
    q = deque([(*start, 0)])
    seen = {(start[0], start[1])}
    while q:
        r, c, d = q.popleft()
        if r == target_row:
            return d
        for nr, nc in _pawn_legal_targets_from_pos(env, player_idx, r, c, h, v):
            if (nr, nc) not in seen:
                seen.add((nr, nc))
                q.append((nr, nc, d + 1))
    return inf


def shortest_path_len_both(env, h_walls=None, v_walls=None):
    cur = env.player
    opp = cur ^ 1
    d_self = shortest_path_len(env, cur, h_walls, v_walls)
    d_opp = shortest_path_len(env, opp, h_walls, v_walls)
    return d_self, d_opp
