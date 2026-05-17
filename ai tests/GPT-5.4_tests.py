import copy
import math
import os
import sys

import numpy as np
import pytest

# Run these tests from the folder containing Quoridor_Class.py, shortest.py, state_encoder.py
HERE = os.path.dirname(__file__)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

from Quoridor_Class import (
    ACTION_H_BASE,
    ACTION_V_BASE,
    BOARD_SIZE,
    MAX_WALLS,
    NUM_ACTIONS,
    QuoridorEnv,
)
from state_encoder import policy_from_canonical, policy_to_canonical, mask_to_canonical


def pawn_action(r, c):
    return r * BOARD_SIZE + c


def h_wall_action(wr, wc):
    return ACTION_H_BASE + wr * (BOARD_SIZE - 1) + wc


def v_wall_action(wr, wc):
    return ACTION_V_BASE + wr * (BOARD_SIZE - 1) + wc


def snapshot(env):
    return {
        "pawns": tuple(env.pawns),
        "walls_h": env.walls_h.copy(),
        "walls_v": env.walls_v.copy(),
        "walls_h_owner": env.walls_h_owner.copy(),
        "walls_v_owner": env.walls_v_owner.copy(),
        "walls_left": tuple(env.walls_left),
        "player": env.player,
        "done": env.done,
        "winner": env.winner,
    }


def assert_same_state(a, b):
    assert a["pawns"] == b["pawns"]
    assert np.array_equal(a["walls_h"], b["walls_h"])
    assert np.array_equal(a["walls_v"], b["walls_v"])
    assert np.array_equal(a["walls_h_owner"], b["walls_h_owner"])
    assert np.array_equal(a["walls_v_owner"], b["walls_v_owner"])
    assert a["walls_left"] == b["walls_left"]
    assert a["player"] == b["player"]
    assert a["done"] == b["done"]
    assert a["winner"] == b["winner"]


def test_reset_contract_and_initial_legal_actions():
    env = QuoridorEnv()
    encoded = env.reset()

    assert env.pawns == [(8, 4), (0, 4)]
    assert env.player == 0
    assert env.done is False
    assert env.winner is None
    assert env.walls_left == [MAX_WALLS, MAX_WALLS]
    assert env.walls_h.shape == (8, 8)
    assert env.walls_v.shape == (8, 8)
    assert encoded.shape == (7, 9, 9)

    mask = env.legal_actions()
    assert mask.shape == (NUM_ACTIONS,)
    assert set(np.flatnonzero(mask[:ACTION_H_BASE])) == {
        pawn_action(7, 4),
        pawn_action(8, 3),
        pawn_action(8, 5),
    }
    assert int(mask[ACTION_H_BASE:ACTION_V_BASE].sum()) == 64
    assert int(mask[ACTION_V_BASE:].sum()) == 64
    assert int(mask.sum()) == 131


def test_apply_and_undo_round_trip_for_pawn_and_wall_actions():
    env = QuoridorEnv()

    before = snapshot(env)
    token = env.apply(pawn_action(7, 4))
    assert env.pawns[0] == (7, 4)
    assert env.player == 1
    env.undo(token)
    assert_same_state(snapshot(env), before)

    before = snapshot(env)
    token = env.apply(h_wall_action(4, 4))
    assert env.walls_h[4, 4] == 1
    assert env.walls_h_owner[4, 4] == 0
    assert env.walls_left[0] == MAX_WALLS - 1
    assert env.player == 1
    env.undo(token)
    assert_same_state(snapshot(env), before)

    before = snapshot(env)
    token = env.apply(v_wall_action(3, 2))
    assert env.walls_v[3, 2] == 1
    assert env.walls_v_owner[3, 2] == 0
    assert env.walls_left[0] == MAX_WALLS - 1
    env.undo(token)
    assert_same_state(snapshot(env), before)


def test_pawn_jump_straight_over_adjacent_opponent():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (3, 4)]
    env.player = 0

    legal = set(np.flatnonzero(env.legal_actions()[:ACTION_H_BASE]))

    assert pawn_action(2, 4) in legal       # straight jump over opponent
    assert pawn_action(3, 4) not in legal   # cannot move onto opponent
    assert pawn_action(5, 4) in legal
    assert pawn_action(4, 3) in legal
    assert pawn_action(4, 5) in legal


def test_pawn_diagonal_jump_when_wall_blocks_straight_jump():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (3, 4)]
    env.player = 0

    # Block the edge between opponent (3,4) and jump target (2,4).
    env.walls_h[2, 3] = 1

    legal = set(np.flatnonzero(env.legal_actions()[:ACTION_H_BASE]))

    assert pawn_action(2, 4) not in legal
    assert pawn_action(3, 3) in legal
    assert pawn_action(3, 5) in legal
    assert pawn_action(3, 4) not in legal


def test_wall_overlap_crossing_and_wall_counter_rules():
    env = QuoridorEnv()

    token = env.apply(h_wall_action(4, 4))
    assert env.walls_left == [9, 10]

    # Same wall, partially overlapping horizontal walls, and crossing vertical wall are illegal.
    assert not env._legal_h_wall(4, 4)
    assert not env._legal_h_wall(4, 3)
    assert not env._legal_h_wall(4, 5)
    assert not env._legal_v_wall(4, 4)

    env.undo(token)
    env.walls_left[0] = 0
    env.player = 0
    mask = env.legal_actions()
    assert int(mask[ACTION_H_BASE:].sum()) == 0
    assert int(mask[:ACTION_H_BASE].sum()) > 0


def test_temporary_wall_path_check_detects_no_path_position():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (0, 0)]
    env.player = 0

    # Contrived near-box around player 0. The temporary wall h=(3,3) closes the last exit.
    env.walls_h[4, 3] = 1  # down blocked from (4,4)
    env.walls_v[4, 3] = 1  # left blocked from (4,4)
    env.walls_v[4, 4] = 1  # right blocked from (4,4)
    env._walls_sig_dirty = True

    assert env._has_path_with_temp(env.pawns[0], 0, temp_h=None, temp_v=None)
    assert not env._check_paths_with_temp_wall(h=(3, 3))


def test_goal_detection_done_mask_and_undo():
    env = QuoridorEnv()
    env.pawns = [(1, 4), (0, 0)]
    env.player = 0

    before = snapshot(env)
    token = env.apply(pawn_action(0, 4))

    assert env.done is True
    assert env.winner == 0
    assert env.player == 0  # terminal move should not switch player
    assert env.legal_actions().sum() == 0

    env.undo(token)
    assert_same_state(snapshot(env), before)


def test_encoder_canonical_rotation_and_policy_round_trip():
    env = QuoridorEnv()
    env.pawns = [(8, 4), (2, 3)]
    env.player = 1
    env.walls_left = [7, 5]

    x = env.encode()
    assert x.shape == (7, 9, 9)
    assert x[0, 6, 5] == 1.0  # current player pawn rotated 180 degrees
    assert x[1, 0, 4] == 1.0  # opponent pawn rotated 180 degrees
    assert np.allclose(x[4], 5 / MAX_WALLS)
    assert np.allclose(x[5], 7 / MAX_WALLS)

    pi = np.arange(NUM_ACTIONS, dtype=np.float32)
    assert np.array_equal(policy_from_canonical(policy_to_canonical(pi, player=1), player=1), pi)

    mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
    mask[pawn_action(2, 3)] = 1.0
    can = mask_to_canonical(mask, player=1)
    assert can[pawn_action(6, 5)] == 1.0


def test_shortest_path_len_works_when_scripts_are_run_directly():
    # This currently exposes a real bug: shortest_path_len uses
    # `from .Quoridor_Class import BOARD_SIZE`, which fails when shortest.py is
    # imported as a plain script instead of as part of a package.
    import shortest

    env = QuoridorEnv()
    assert shortest.shortest_path_len(env, 0) == 8
    assert shortest.shortest_path_len(env, 1) == 8


@pytest.mark.xfail(reason="Current apply() trusts caller and does not validate action legality.")
def test_apply_should_not_accept_illegal_actions_without_validation():
    env = QuoridorEnv()
    illegal = pawn_action(0, 0)  # player 0 cannot teleport from (8,4) to (0,0)
    assert not env.is_legal(illegal)

    with pytest.raises((ValueError, AssertionError)):
        env.apply(illegal)
