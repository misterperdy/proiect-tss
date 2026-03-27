import numpy as np
from .Quoridor_Class import BOARD_SIZE, NUM_ACTIONS, ACTION_H_BASE, ACTION_V_BASE


def _rot180_rc(r, c):
    return (BOARD_SIZE - 1 - r, BOARD_SIZE - 1 - c)


def _rot180_wall(wr, wc):
    wall_grid_max = BOARD_SIZE - 2
    return (wall_grid_max - wr, wall_grid_max - wc)


_perm_env_to_canon = np.arange(NUM_ACTIONS, dtype=np.int32)

for r in range(BOARD_SIZE):
    for c in range(BOARD_SIZE):
        env_idx = r * BOARD_SIZE + c
        r2, c2 = _rot180_rc(r, c)
        _perm_env_to_canon[env_idx] = r2 * BOARD_SIZE + c2

wall_grid_size = BOARD_SIZE - 1
for wr in range(wall_grid_size):
    for wc in range(wall_grid_size):
        env_idx = ACTION_H_BASE + wr * wall_grid_size + wc
        wr2, wc2 = _rot180_wall(wr, wc)
        _perm_env_to_canon[env_idx] = ACTION_H_BASE + wr2 * wall_grid_size + wc2

for wr in range(wall_grid_size):
    for wc in range(wall_grid_size):
        env_idx = ACTION_V_BASE + wr * wall_grid_size + wc
        wr2, wc2 = _rot180_wall(wr, wc)
        _perm_env_to_canon[env_idx] = ACTION_V_BASE + wr2 * wall_grid_size + wc2

_perm_canon_to_env = _perm_env_to_canon.copy()


def policy_to_canonical(pi_env, player):
    if player == 0:
        return pi_env
    return pi_env[_perm_env_to_canon]


def policy_from_canonical(pi_can, player):
    if player == 0:
        return pi_can
    out = np.zeros_like(pi_can)
    out[_perm_canon_to_env] = pi_can
    return out


def mask_to_canonical(mask_env, player):
    if player == 0:
        return mask_env
    return mask_env[_perm_env_to_canon]


def encode_state(env):
    planes = []
    cur = env.player
    opp = cur ^ 1
    (cr, cc) = env.pawns[cur]
    (or_, oc) = env.pawns[opp]

    c0 = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    c0[cr, cc] = 1.0
    planes.append(c0)

    c1 = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    c1[or_, oc] = 1.0
    planes.append(c1)

    wall_grid_size = BOARD_SIZE - 1
    c2 = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    c2[:wall_grid_size, :wall_grid_size] = env.walls_h
    c2[:wall_grid_size, 1:BOARD_SIZE] = np.maximum(c2[:wall_grid_size, 1:BOARD_SIZE], env.walls_h)
    planes.append(c2)

    c3 = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    c3[:wall_grid_size, :wall_grid_size] = env.walls_v
    c3[1:BOARD_SIZE, :wall_grid_size] = np.maximum(c3[1:BOARD_SIZE, :wall_grid_size], env.walls_v)
    planes.append(c3)

    from Quoridor_Class import MAX_WALLS
    planes.append(np.full((BOARD_SIZE, BOARD_SIZE), env.walls_left[cur] / float(MAX_WALLS), dtype=np.float32))
    planes.append(np.full((BOARD_SIZE, BOARD_SIZE), env.walls_left[opp] / float(MAX_WALLS), dtype=np.float32))

    c6 = np.zeros((BOARD_SIZE, BOARD_SIZE), dtype=np.float32)
    if cur == 0:
        c6[0, :] = 1.0
    else:
        c6[BOARD_SIZE - 1, :] = 1.0
    planes.append(c6)

    return np.stack(planes, axis=0)


def encode_state_canonical(env):
    x_abs = encode_state(env)
    if env.player == 0:
        return x_abs
    return np.rot90(x_abs, 2, axes=(1, 2)).copy()
