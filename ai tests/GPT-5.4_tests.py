"""
Core pytest suite for QuoridorEnv.
Place this file next to:
  - Quoridor_Class.py
  - shortest.py
  - state_encoder.py
Run with:
  python -m pytest -q test_quoridor_env_core.py
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

# Make the tests runnable when this file is placed beside the source files.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from Quoridor_Class import (  # noqa: E402
    QuoridorEnv,
    BOARD_SIZE,
    MAX_WALLS,
    ACTION_H_BASE,
    ACTION_V_BASE,
    NUM_ACTIONS,
)
from state_encoder import (  # noqa: E402
    encode_state,
    policy_from_canonical,
    policy_to_canonical,
    mask_to_canonical,
)


def pawn_action(r: int, c: int) -> int:
    return r * BOARD_SIZE + c


def h_wall_action(wr: int, wc: int) -> int:
    return ACTION_H_BASE + wr * (BOARD_SIZE - 1) + wc


def v_wall_action(wr: int, wc: int) -> int:
    return ACTION_V_BASE + wr * (BOARD_SIZE - 1) + wc


def state_snapshot(env: QuoridorEnv):
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


def assert_same_state(env: QuoridorEnv, snap):
    assert tuple(env.pawns) == snap["pawns"]
    np.testing.assert_array_equal(env.walls_h, snap["walls_h"])
    np.testing.assert_array_equal(env.walls_v, snap["walls_v"])
    np.testing.assert_array_equal(env.walls_h_owner, snap["walls_h_owner"])
    np.testing.assert_array_equal(env.walls_v_owner, snap["walls_v_owner"])
    assert tuple(env.walls_left) == snap["walls_left"]
    assert env.player == snap["player"]
    assert env.done == snap["done"]
    assert env.winner == snap["winner"]


def test_reset_initial_state_and_legal_action_contract():
    env = QuoridorEnv()

    assert env.pawns == [(8, 4), (0, 4)]
    assert env.walls_left == [MAX_WALLS, MAX_WALLS]
    assert env.player == 0
    assert not env.done
    assert env.winner is None

    obs = env.encode()
    assert obs.shape == (7, BOARD_SIZE, BOARD_SIZE)
    assert obs.dtype == np.float32

    mask = env.legal_actions()
    assert mask.shape == (NUM_ACTIONS,)
    assert mask.dtype == np.float32
    assert set(np.unique(mask)).issubset({0.0, 1.0})

    legal_pawn_actions = {i for i in range(BOARD_SIZE * BOARD_SIZE) if mask[i] == 1.0}
    assert legal_pawn_actions == {
        pawn_action(7, 4),
        pawn_action(8, 3),
        pawn_action(8, 5),
    }

    # Empty board: all wall positions should be legal, plus 3 pawn moves.
    assert int(mask.sum()) == 3 + 64 + 64


def test_step_legal_pawn_move_switches_player_without_reward():
    env = QuoridorEnv()
    obs, reward, done, info = env.step(pawn_action(7, 4))

    assert env.pawns[0] == (7, 4)
    assert env.player == 1
    assert reward == 0.0
    assert not done
    assert info == {}
    assert obs.shape == (7, BOARD_SIZE, BOARD_SIZE)


def test_illegal_move_loses_immediately_and_marks_info():
    env = QuoridorEnv()

    # From the initial state, player 0 cannot teleport to the top-left corner.
    _, reward, done, info = env.step(pawn_action(0, 0))

    assert done is True
    assert reward == -1.0
    assert info == {"illegal": True}
    assert env.done is True
    assert env.winner == 1


def test_step_after_game_finished_raises_runtime_error():
    env = QuoridorEnv()
    env.step(pawn_action(0, 0))  # illegal -> ends game

    with pytest.raises(RuntimeError):
        env.step(pawn_action(7, 4))


def test_reaching_goal_ends_game_with_positive_reward():
    env = QuoridorEnv()
    env.pawns = [(1, 4), (8, 4)]
    env.player = 0

    _, reward, done, info = env.step(pawn_action(0, 4))

    assert done is True
    assert reward == 1.0
    assert info == {}
    assert env.winner == 0
    assert env.player == 0  # Terminal move should not switch turn.


def test_no_wall_actions_when_current_player_has_no_walls_left():
    env = QuoridorEnv()
    env.walls_left[0] = 0

    mask = env.legal_actions()

    assert mask[ACTION_H_BASE:].sum() == 0.0
    assert mask[:ACTION_H_BASE].sum() == 3.0


def test_wall_overlap_and_crossing_rules_are_enforced():
    env = QuoridorEnv()
    env.walls_h[3, 3] = 1
    env.walls_h_owner[3, 3] = 0
    env._walls_sig_dirty = True

    # Same horizontal wall and adjacent horizontal walls overlap a length-2 wall.
    assert not env._legal_h_wall(3, 3)
    assert not env._legal_h_wall(3, 2)
    assert not env._legal_h_wall(3, 4)

    # A vertical wall at the same grid coordinate crosses the horizontal wall.
    assert not env._legal_v_wall(3, 3)


def test_walls_block_pawn_movement_edges():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (0, 4)]
    env.player = 0

    assert pawn_action(3, 4) in np.flatnonzero(env.legal_actions())

    # Horizontal wall at (3, 3) blocks vertical movement between rows 3 and 4
    # for columns 3 and 4.
    env.walls_h[3, 3] = 1
    env._walls_sig_dirty = True

    assert pawn_action(3, 4) not in np.flatnonzero(env.legal_actions())
    assert pawn_action(4, 3) in np.flatnonzero(env.legal_actions())
    assert pawn_action(4, 5) in np.flatnonzero(env.legal_actions())
    assert pawn_action(5, 4) in np.flatnonzero(env.legal_actions())


def test_pawn_jump_straight_when_opponent_adjacent_and_no_wall_behind():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (3, 4)]
    env.player = 0

    legal = set(np.flatnonzero(env.legal_actions()))

    assert pawn_action(2, 4) in legal      # jump over opponent
    assert pawn_action(3, 4) not in legal  # cannot move onto opponent


def test_pawn_diagonal_jump_when_wall_blocks_straight_jump():
    env = QuoridorEnv()
    env.pawns = [(4, 4), (3, 4)]
    env.player = 0

    # Block the edge behind the opponent: between (3, 4) and (2, 4).
    env.walls_h[2, 3] = 1
    env._walls_sig_dirty = True

    legal = set(np.flatnonzero(env.legal_actions()))

    assert pawn_action(2, 4) not in legal
    assert pawn_action(3, 3) in legal
    assert pawn_action(3, 5) in legal
    assert pawn_action(3, 4) not in legal


def test_apply_and_undo_restore_exact_state_for_pawn_and_wall_actions():
    env = QuoridorEnv()

    snap = state_snapshot(env)
    token = env.apply(pawn_action(7, 4))
    env.undo(token)
    assert_same_state(env, snap)

    snap = state_snapshot(env)
    token = env.apply(h_wall_action(2, 2))
    env.undo(token)
    assert_same_state(env, snap)

    snap = state_snapshot(env)
    token = env.apply(v_wall_action(5, 5))
    env.undo(token)
    assert_same_state(env, snap)


def test_clone_is_independent_after_mutation():
    env = QuoridorEnv()
    token = env.apply(h_wall_action(2, 2))
    assert env.player == 1

    clone = env.clone()
    clone.walls_h[2, 2] = 0
    clone.pawns[0] = (7, 4)
    clone.walls_left[0] = 99

    assert env.walls_h[2, 2] == 1
    assert env.pawns[0] == (8, 4)
    assert env.walls_left[0] == 9
    env.undo(token)


@pytest.mark.xfail(reason="clone() currently copies wall arrays but not wall owner arrays.")
def test_clone_preserves_wall_owner_metadata():
    env = QuoridorEnv()
    env.apply(h_wall_action(2, 2))

    clone = env.clone()

    assert clone.walls_h[2, 2] == 1
    assert clone.walls_h_owner[2, 2] == 0


def test_canonical_encoding_rotates_player_one_position():
    env = QuoridorEnv()
    env.pawns = [(6, 2), (2, 6)]
    env.walls_left = [7, 4]
    env.player = 1

    absolute = encode_state(env)
    canonical = env.encode()

    np.testing.assert_array_equal(canonical, np.rot90(absolute, 2, axes=(1, 2)).copy())
    assert canonical.shape == (7, BOARD_SIZE, BOARD_SIZE)


def test_policy_and_mask_canonical_round_trip_for_player_one():
    pi_env = np.arange(NUM_ACTIONS, dtype=np.float32)
    pi_can = policy_to_canonical(pi_env, player=1)
    round_trip = policy_from_canonical(pi_can, player=1)

    np.testing.assert_array_equal(round_trip, pi_env)

    mask_env = np.zeros(NUM_ACTIONS, dtype=np.float32)
    mask_env[[pawn_action(7, 4), h_wall_action(1, 2), v_wall_action(3, 4)]] = 1.0
    mask_can = mask_to_canonical(mask_env, player=1)
    assert mask_can.sum() == mask_env.sum()


def test_fast_path_checker_detects_no_path_in_artificially_sealed_state():
    env = QuoridorEnv()
    env.pawns = [(8, 4), (0, 4)]

    # Artificial barrier between rows 7 and 8 with one gap at column 4.
    # This directly tests the path checker, not legal wall construction history.
    for wc in [0, 2, 5, 7]:
        env.walls_h[7, wc] = 1
    env._walls_sig_dirty = True

    assert env._has_path_with_temp(env.pawns[0], 0) is True
    assert env._has_path_with_temp(env.pawns[0], 0, temp_h=(7, 3)) is False
    assert env._check_paths_with_temp_wall(h=(7, 3)) is False


@pytest.mark.xfail(reason="step() wall path currently does not set _walls_sig_dirty after wall placement.")
def test_step_wall_action_invalidates_cached_wall_signature():
    env = QuoridorEnv()
    before = env._get_walls_sig()
    assert env._walls_sig_dirty is False

    _, reward, done, info = env.step(h_wall_action(0, 0))

    assert reward == 0.0
    assert not done
    assert info == {}
    after = env._get_walls_sig()
    assert after != before


@pytest.mark.xfail(reason="is_legal() directly indexes legal_actions(); out-of-range actions currently raise IndexError.")
@pytest.mark.parametrize("bad_action", [-1, NUM_ACTIONS])
def test_invalid_action_ids_are_handled_as_illegal_not_index_errors(bad_action):
    env = QuoridorEnv()

    _, reward, done, info = env.step(bad_action)

    assert done is True
    assert reward == -1.0
    assert info == {"illegal": True}
    assert env.winner == 1


@pytest.mark.xfail(reason="shortest_path_len uses a package-relative import that fails when scripts are run as top-level files.")
def test_shortest_path_len_helper_runs_when_scripts_are_top_level():
    from shortest import shortest_path_len

    env = QuoridorEnv()
    assert shortest_path_len(env, 0) == 8
    assert shortest_path_len(env, 1) == 8
