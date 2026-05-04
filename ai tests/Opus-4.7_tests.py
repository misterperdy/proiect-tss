"""
Test suite for QuoridorEnv (Quoridor_Class.py + state_encoder.py + shortest.py).

The suite focuses on:
  1. Action-space encoding and legal-mask shape/values.
  2. Pawn movement, including the jump rules (the most error-prone Quoridor sub-system).
  3. Wall placement validation: overlap, cross, budget, path-existence rule.
  4. Goal detection and termination semantics (win, illegal-loss, draw, post-done step).
  5. Apply/undo reversibility -- critical for MCTS / AlphaZero search.
  6. Clone independence.
  7. State-encoder shape and the canonical-perspective rotation.
  8. Policy <-> canonical permutation round-trip.
  9. A randomized smoke test that drives many games to termination under the legal mask.

Run with:  pytest test_quoridor.py -v
"""
import numpy as np
import pytest

from Quoridor_Class import (
    QuoridorEnv,
    BOARD_SIZE,
    MAX_WALLS,
    NUM_ACTIONS,
    ACTION_H_BASE,
    ACTION_V_BASE,
    NUM_PAWN_ACTIONS,
    NUM_H_WALLS,
    NUM_V_WALLS,
)
from state_encoder import (
    encode_state,
    encode_state_canonical,
    policy_to_canonical,
    policy_from_canonical,
    mask_to_canonical,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def pawn_action(r, c):
    return r * BOARD_SIZE + c


def h_wall_action(wr, wc):
    return ACTION_H_BASE + wr * (BOARD_SIZE - 1) + wc


def v_wall_action(wr, wc):
    return ACTION_V_BASE + wr * (BOARD_SIZE - 1) + wc


def fresh_env():
    return QuoridorEnv()


# ---------------------------------------------------------------------------
# 1. Action-space encoding
# ---------------------------------------------------------------------------

class TestActionSpace:
    """Catches off-by-one errors in the index layout used everywhere downstream."""

    def test_constants_match_board_size(self):
        wgs = BOARD_SIZE - 1  # wall-grid size
        assert NUM_PAWN_ACTIONS == BOARD_SIZE * BOARD_SIZE
        assert NUM_H_WALLS == wgs * wgs
        assert NUM_V_WALLS == wgs * wgs
        assert ACTION_H_BASE == NUM_PAWN_ACTIONS
        assert ACTION_V_BASE == ACTION_H_BASE + NUM_H_WALLS
        assert NUM_ACTIONS == ACTION_V_BASE + NUM_V_WALLS

    def test_action_helpers_invertible(self):
        # Pawn action endpoints
        assert pawn_action(0, 0) == 0
        assert pawn_action(BOARD_SIZE - 1, BOARD_SIZE - 1) == NUM_PAWN_ACTIONS - 1
        # Wall action endpoints sit just inside their slabs
        assert h_wall_action(0, 0) == ACTION_H_BASE
        assert h_wall_action(BOARD_SIZE - 2, BOARD_SIZE - 2) == ACTION_V_BASE - 1
        assert v_wall_action(0, 0) == ACTION_V_BASE
        assert v_wall_action(BOARD_SIZE - 2, BOARD_SIZE - 2) == NUM_ACTIONS - 1


# ---------------------------------------------------------------------------
# 2. Reset / initial state
# ---------------------------------------------------------------------------

class TestReset:
    def test_initial_pawn_positions(self):
        env = fresh_env()
        # Player 0 starts at the bottom row, Player 1 at the top, both centered.
        assert env.pawns[0] == (BOARD_SIZE - 1, BOARD_SIZE // 2)
        assert env.pawns[1] == (0, BOARD_SIZE // 2)

    def test_initial_metadata(self):
        env = fresh_env()
        assert env.player == 0
        assert env.done is False
        assert env.winner is None
        assert env.walls_left == [MAX_WALLS, MAX_WALLS]
        assert env.walls_h.shape == (BOARD_SIZE - 1, BOARD_SIZE - 1)
        assert env.walls_v.shape == (BOARD_SIZE - 1, BOARD_SIZE - 1)
        assert env.walls_h.sum() == 0 and env.walls_v.sum() == 0
        # Wall ownership grids should start empty (-1 = unowned).
        assert (env.walls_h_owner == -1).all()
        assert (env.walls_v_owner == -1).all()

    def test_reset_with_custom_walls_left(self):
        env = QuoridorEnv()
        env.reset(walls_left=[3, 5])
        assert env.walls_left == [3, 5]
        # Custom walls_left must not bleed back into MAX_WALLS or shared state.
        env2 = QuoridorEnv()
        assert env2.walls_left == [MAX_WALLS, MAX_WALLS]


# ---------------------------------------------------------------------------
# 3. legal_actions() shape and values
# ---------------------------------------------------------------------------

class TestLegalMask:
    def test_mask_shape_and_dtype(self):
        env = fresh_env()
        mask = env.legal_actions()
        assert mask.shape == (NUM_ACTIONS,)
        assert mask.dtype == np.float32

    def test_mask_is_binary(self):
        env = fresh_env()
        mask = env.legal_actions()
        assert set(np.unique(mask).tolist()).issubset({0.0, 1.0})

    def test_initial_legal_count(self):
        # P0 at (8,4) has 3 pawn moves (up, left, right). Both wall slabs are fully
        # legal at start (no overlaps/crosses, paths exist). Total = 3 + 64 + 64 = 131.
        env = fresh_env()
        assert int(env.legal_actions().sum()) == 3 + NUM_H_WALLS + NUM_V_WALLS

    def test_mask_zero_after_done(self):
        env = fresh_env()
        env.done = True
        mask = env.legal_actions()
        assert mask.sum() == 0.0


# ---------------------------------------------------------------------------
# 4. Pawn movement (basic + jump rules)
# ---------------------------------------------------------------------------

def _legal_pawn_targets(env):
    """Pull legal pawn destinations as (r,c) pairs from the legal mask."""
    mask = env.legal_actions()
    return {(i // BOARD_SIZE, i % BOARD_SIZE) for i in range(NUM_PAWN_ACTIONS) if mask[i] == 1.0}


class TestPawnMovement:
    def test_corner_pawn_has_two_moves(self):
        env = fresh_env()
        env.pawns = [(BOARD_SIZE - 1, 0), (0, 0)]  # P0 at SW corner, P1 at NW corner
        env.player = 0
        targets = _legal_pawn_targets(env)
        # From (8,0): up to (7,0) and right to (8,1) only.
        assert targets == {(BOARD_SIZE - 2, 0), (BOARD_SIZE - 1, 1)}

    def test_pawn_blocked_by_wall(self):
        env = fresh_env()
        # H wall (7, 3) blocks vertical moves (7,3)-(8,3) and (7,4)-(8,4).
        env.walls_h[7, 3] = 1
        # Default P0 at (8, 4) -- up is now blocked.
        targets = _legal_pawn_targets(env)
        assert (7, 4) not in targets
        # Sideways and other directions remain.
        assert (8, 3) in targets and (8, 5) in targets

    def test_pawn_cannot_step_onto_opponent(self):
        env = fresh_env()
        env.pawns = [(5, 4), (4, 4)]  # adjacent
        env.player = 0
        targets = _legal_pawn_targets(env)
        assert (4, 4) not in targets, "Stepping onto opponent's square must be illegal."


class TestPawnJumpRules:
    """The Quoridor jump rules are the single most error-prone sub-system."""

    def test_simple_jump_over_opponent(self):
        env = fresh_env()
        env.pawns = [(5, 4), (4, 4)]
        env.player = 0
        targets = _legal_pawn_targets(env)
        # No wall behind opponent => P0 jumps straight to (3, 4).
        assert (3, 4) in targets
        # Diagonals must NOT be available when a straight jump is possible.
        assert (4, 3) not in targets
        assert (4, 5) not in targets

    def test_diagonal_jump_when_wall_blocks_straight(self):
        env = fresh_env()
        env.pawns = [(5, 4), (4, 4)]
        env.player = 0
        # H wall (3, 3) blocks (3,4)-(4,4): the straight jump destination.
        env.walls_h[3, 3] = 1
        targets = _legal_pawn_targets(env)
        # Straight jump now blocked; sideways diagonals must be enabled.
        assert (3, 4) not in targets
        assert (4, 3) in targets
        assert (4, 5) in targets

    def test_diagonal_jump_when_opponent_at_edge(self):
        env = fresh_env()
        env.pawns = [(1, 4), (0, 4)]  # P1 on the top edge
        env.player = 0
        targets = _legal_pawn_targets(env)
        # Straight jump would land on row -1 (off-board); diagonals must be allowed.
        assert (0, 3) in targets and (0, 5) in targets

    def test_jump_does_not_return_to_self(self):
        env = fresh_env()
        env.pawns = [(5, 4), (4, 4)]
        env.player = 0
        targets = _legal_pawn_targets(env)
        # Even if some diagonal logic would land on (cr, cc), the env must filter it.
        assert (5, 4) not in targets


# ---------------------------------------------------------------------------
# 5. Wall placement validation
# ---------------------------------------------------------------------------

class TestWallPlacement:
    def test_overlap_horizontal_walls_rejected(self):
        env = fresh_env()
        env.walls_h[3, 3] = 1
        # An H-wall sharing any cell with (3,3) overlaps: (3,2) and (3,4).
        assert env._legal_h_wall(3, 3) is False, "Same slot must overlap."
        assert env._legal_h_wall(3, 2) is False, "Adjacent slot overlaps cell (3,3)."
        assert env._legal_h_wall(3, 4) is False, "Adjacent slot overlaps cell (3,4)."
        # Two slots away is fine.
        assert env._legal_h_wall(3, 5) is True
        # Different row entirely: no overlap.
        assert env._legal_h_wall(4, 3) is True

    def test_overlap_vertical_walls_rejected(self):
        env = fresh_env()
        env.walls_v[3, 3] = 1
        assert env._legal_v_wall(3, 3) is False
        assert env._legal_v_wall(2, 3) is False
        assert env._legal_v_wall(4, 3) is False
        assert env._legal_v_wall(5, 3) is True
        assert env._legal_v_wall(3, 4) is True

    def test_perpendicular_walls_cannot_cross(self):
        env = fresh_env()
        env.walls_h[3, 3] = 1
        # A V-wall at the same (3,3) intersection crosses the H-wall.
        assert env._legal_v_wall(3, 3) is False
        # Different intersections must remain legal.
        assert env._legal_v_wall(3, 4) is True
        assert env._legal_v_wall(4, 3) is True

    def test_wall_budget_enforced(self):
        env = fresh_env()
        env.walls_left[0] = 0  # current player exhausted walls
        mask = env.legal_actions()
        # No wall actions of either orientation may be legal.
        assert mask[ACTION_H_BASE:].sum() == 0.0
        # Pawn moves must still be available.
        assert mask[:ACTION_H_BASE].sum() > 0

    def test_path_blocking_wall_is_illegal(self):
        """The defining Quoridor rule: a wall that traps a player must be rejected."""
        env = fresh_env()
        # Trap-construction: P0 at (8,8). H wall (7,7) blocks (7,7)-(8,7) and (7,8)-(8,8).
        # P0's only escape is then (8,7). A V wall at (7,6) blocks (8,6)-(8,7),
        # which fully traps P0 in (8,8).
        env.pawns = [(BOARD_SIZE - 1, BOARD_SIZE - 1), (0, 0)]
        env.walls_h[BOARD_SIZE - 2, BOARD_SIZE - 2] = 1  # (7, 7)
        assert env._legal_v_wall(BOARD_SIZE - 2, BOARD_SIZE - 3) is False, (
            "Wall that completely traps a pawn must be illegal."
        )
        # Sanity: a non-trapping V-wall in the same neighbourhood is still legal.
        assert env._legal_v_wall(BOARD_SIZE - 2, BOARD_SIZE - 4) is True

    def test_wall_out_of_bounds(self):
        env = fresh_env()
        wgs = BOARD_SIZE - 1
        # Indices on or past the wall-grid edge must be rejected.
        assert env._legal_h_wall(wgs, 0) is False
        assert env._legal_h_wall(0, wgs) is False
        assert env._legal_h_wall(-1, 0) is False


# ---------------------------------------------------------------------------
# 6. Goal detection / termination
# ---------------------------------------------------------------------------

class TestTermination:
    def test_player0_wins_at_row_0(self):
        env = fresh_env()
        env.pawns = [(1, 4), (0, 0)]  # P0 one step from goal
        env.player = 0
        obs, reward, done, info = env.step(pawn_action(0, 4))
        assert done is True
        assert env.winner == 0
        assert reward == 1.0
        # When the game ends on a winning move, the player must NOT be flipped.
        assert env.player == 0

    def test_player1_wins_at_row_8(self):
        env = fresh_env()
        env.pawns = [(8, 0), (BOARD_SIZE - 2, 4)]  # P1 one step from goal
        env.player = 1
        obs, reward, done, info = env.step(pawn_action(BOARD_SIZE - 1, 4))
        assert done is True
        assert env.winner == 1
        assert reward == 1.0

    def test_illegal_action_immediately_loses(self):
        env = fresh_env()
        # P0 at (8,4) can't move to (0,0) in one step -> illegal.
        obs, reward, done, info = env.step(pawn_action(0, 0))
        assert done is True
        assert env.winner == 1, "Opponent must be declared winner on illegal move."
        assert reward == -1.0
        assert info.get("illegal") is True

    def test_step_after_done_raises(self):
        env = fresh_env()
        env.done = True
        with pytest.raises(RuntimeError):
            env.step(pawn_action(7, 4))

    def test_threefold_repetition_draws(self):
        """Shuffle the same two pawns back and forth; on the 3rd repeat, game is a draw."""
        env = fresh_env()
        # Move both pawns away from the centre column so they never collide.
        env.pawns = [(8, 0), (0, 8)]
        env.player = 0
        moves = [
            pawn_action(7, 0),  # P0
            pawn_action(1, 8),  # P1
            pawn_action(8, 0),  # P0 back
            pawn_action(0, 8),  # P1 back  <-- 1st repeat of starting position (post-P1)
            pawn_action(7, 0),
            pawn_action(1, 8),
            pawn_action(8, 0),
            pawn_action(0, 8),  # 2nd repeat
            pawn_action(7, 0),
            pawn_action(1, 8),
            pawn_action(8, 0),
            pawn_action(0, 8),  # 3rd repeat -> draw
        ]
        last = None
        for a in moves:
            last = env.step(a)
            if last[2]:
                break
        obs, reward, done, info = last
        assert done is True
        assert env.winner is None, "3-fold repetition must be a draw (winner=None)."
        assert reward == 0.0


# ---------------------------------------------------------------------------
# 7. apply / undo reversibility (critical for MCTS)
# ---------------------------------------------------------------------------

class TestApplyUndo:
    def _snapshot(self, env):
        return (
            list(env.pawns),
            env.walls_h.copy(),
            env.walls_v.copy(),
            env.walls_h_owner.copy(),
            env.walls_v_owner.copy(),
            list(env.walls_left),
            env.player,
            env.done,
            env.winner,
        )

    def _equal(self, a, b):
        return (
            a[0] == b[0]
            and np.array_equal(a[1], b[1])
            and np.array_equal(a[2], b[2])
            and np.array_equal(a[3], b[3])
            and np.array_equal(a[4], b[4])
            and a[5] == b[5]
            and a[6] == b[6]
            and a[7] == b[7]
            and a[8] == b[8]
        )

    def test_pawn_apply_undo(self):
        env = fresh_env()
        before = self._snapshot(env)
        token = env.apply(pawn_action(7, 4))
        assert env.pawns[0] == (7, 4)
        env.undo(token)
        assert self._equal(self._snapshot(env), before)

    def test_h_wall_apply_undo(self):
        env = fresh_env()
        before = self._snapshot(env)
        token = env.apply(h_wall_action(3, 3))
        assert env.walls_h[3, 3] == 1
        assert env.walls_h_owner[3, 3] == 0
        assert env.walls_left[0] == MAX_WALLS - 1
        env.undo(token)
        assert self._equal(self._snapshot(env), before)

    def test_v_wall_apply_undo(self):
        env = fresh_env()
        before = self._snapshot(env)
        token = env.apply(v_wall_action(2, 5))
        assert env.walls_v[2, 5] == 1
        assert env.walls_v_owner[2, 5] == 0
        env.undo(token)
        assert self._equal(self._snapshot(env), before)

    def test_winning_apply_undo_restores_done_and_player(self):
        env = fresh_env()
        env.pawns = [(1, 4), (0, 0)]  # P0 one step from goal
        env.player = 0
        before = self._snapshot(env)
        token = env.apply(pawn_action(0, 4))
        # The win must update state.
        assert env.done is True and env.winner == 0
        # And undo must roll all of it back including done/winner/player.
        env.undo(token)
        assert self._equal(self._snapshot(env), before)

    def test_apply_undo_chain_of_random_legal_actions(self):
        """Stress the apply/undo invariants with a deeper stack."""
        rng = np.random.default_rng(0)
        env = fresh_env()
        before = self._snapshot(env)
        tokens = []
        for _ in range(10):
            mask = env.legal_actions()
            if mask.sum() == 0 or env.done:
                break
            choice = int(rng.choice(np.flatnonzero(mask)))
            tokens.append(env.apply(choice))
            if env.done:
                break
        # Unwind in reverse and check we're back to the start.
        for t in reversed(tokens):
            env.undo(t)
        assert self._equal(self._snapshot(env), before)


# ---------------------------------------------------------------------------
# 8. Clone independence
# ---------------------------------------------------------------------------

class TestClone:
    def test_clone_is_independent(self):
        env = fresh_env()
        env.step(pawn_action(7, 4))  # P0 moves up
        clone = env.clone()
        assert clone.pawns == env.pawns
        assert np.array_equal(clone.walls_h, env.walls_h)
        # Mutate the clone -- the original must not change.
        clone.walls_h[0, 0] = 1
        clone.pawns[0] = (0, 0)
        clone.walls_left[0] = 0
        assert env.walls_h[0, 0] == 0
        assert env.pawns[0] == (7, 4)
        assert env.walls_left[0] == MAX_WALLS

    def test_clone_starts_from_same_legal_mask(self):
        env = fresh_env()
        env.step(h_wall_action(3, 3))
        clone = env.clone()
        assert np.array_equal(clone.legal_actions(), env.legal_actions())


# ---------------------------------------------------------------------------
# 9. State encoder
# ---------------------------------------------------------------------------

class TestEncoder:
    def test_encode_shape_and_dtype(self):
        env = fresh_env()
        x = env.encode()
        assert x.shape == (7, BOARD_SIZE, BOARD_SIZE)
        assert x.dtype == np.float32

    def test_my_pawn_and_opp_pawn_planes(self):
        env = fresh_env()
        x = encode_state(env)  # absolute (non-canonical) view
        cr, cc = env.pawns[0]
        orr, occ = env.pawns[1]
        # Channel 0 = current player pawn, Channel 1 = opponent pawn.
        assert x[0, cr, cc] == 1.0 and x[0].sum() == 1.0
        assert x[1, orr, occ] == 1.0 and x[1].sum() == 1.0

    def test_walls_left_planes_are_normalized(self):
        env = fresh_env()
        env.walls_left = [3, 7]
        env.player = 0
        x = encode_state(env)
        # Channel 4 is current-player walls / MAX_WALLS, channel 5 is opponent's.
        assert np.allclose(x[4], 3 / MAX_WALLS)
        assert np.allclose(x[5], 7 / MAX_WALLS)

    def test_canonical_is_identity_for_player_0(self):
        env = fresh_env()
        env.step(pawn_action(7, 4))  # now player flips to 1
        env.player = 0  # force perspective back to P0 for this test
        assert np.allclose(encode_state(env), encode_state_canonical(env))

    def test_canonical_is_180_rotation_for_player_1(self):
        env = fresh_env()
        env.player = 1
        x_abs = encode_state(env)
        x_can = encode_state_canonical(env)
        # 180-degree rotation along (H, W) axes for every plane.
        assert np.allclose(x_can, np.rot90(x_abs, 2, axes=(1, 2)))

    def test_canonical_goal_row_is_top_for_current_player(self):
        """Channel 6 marks the current player's goal row. In canonical view that row is 0."""
        env = fresh_env()
        env.player = 1
        x_can = encode_state_canonical(env)
        # In canonical view P1's goal (originally row 8) becomes row 0.
        assert x_can[6, 0, :].sum() == BOARD_SIZE
        assert x_can[6, 1:, :].sum() == 0


class TestPolicyPermutation:
    def test_round_trip_player_0_is_identity(self):
        rng = np.random.default_rng(1)
        pi = rng.random(NUM_ACTIONS).astype(np.float32)
        back = policy_from_canonical(policy_to_canonical(pi, 0), 0)
        assert np.array_equal(pi, back)

    def test_round_trip_player_1_is_identity(self):
        rng = np.random.default_rng(2)
        pi = rng.random(NUM_ACTIONS).astype(np.float32)
        back = policy_from_canonical(policy_to_canonical(pi, 1), 1)
        assert np.allclose(pi, back)

    def test_pawn_action_permutation_is_180_rot(self):
        """For P1 the canonical action for cell (r,c) must be cell (8-r, 8-c)."""
        pi = np.zeros(NUM_ACTIONS, dtype=np.float32)
        pi[pawn_action(2, 3)] = 1.0  # mark a single pawn cell in env coords
        pi_can = policy_to_canonical(pi, 1)
        rotated_idx = pawn_action(BOARD_SIZE - 1 - 2, BOARD_SIZE - 1 - 3)
        assert pi_can[rotated_idx] == 1.0
        # The original index should now be empty.
        assert pi_can[pawn_action(2, 3)] == 0.0

    def test_mask_to_canonical_preserves_total(self):
        env = fresh_env()
        env.player = 1
        mask = env.legal_actions()
        mask_can = mask_to_canonical(mask, env.player)
        assert mask_can.sum() == mask.sum()


# ---------------------------------------------------------------------------
# 10. Smoke test: random self-play under the legal mask
# ---------------------------------------------------------------------------

class TestRandomPlaySmoke:
    def test_random_games_terminate_cleanly(self):
        rng = np.random.default_rng(42)
        n_games = 25
        max_steps = 400
        terminations = {"win0": 0, "win1": 0, "draw": 0, "illegal": 0, "stalled": 0}

        for _ in range(n_games):
            env = fresh_env()
            for _ in range(max_steps):
                if env.done:
                    break
                mask = env.legal_actions()
                legal_idx = np.flatnonzero(mask)
                if len(legal_idx) == 0:
                    terminations["stalled"] += 1
                    break
                # Bias the random policy slightly towards forward pawn moves so games
                # actually finish; otherwise pure random play often runs the wall budget
                # out without progress.
                fwd = env.forward_pawn_actions()
                if fwd and rng.random() < 0.6:
                    a = int(rng.choice(fwd))
                else:
                    a = int(rng.choice(legal_idx))
                env.step(a)

            if env.done:
                if env.winner == 0:
                    terminations["win0"] += 1
                elif env.winner == 1:
                    terminations["win1"] += 1
                else:
                    terminations["draw"] += 1

        # Every game must have terminated cleanly under the (possibly truncated) rollout.
        assert sum(terminations.values()) == n_games
        # And we expect at least *some* genuine wins to occur with the forward bias.
        assert terminations["win0"] + terminations["win1"] > 0


if __name__ == "__main__":
    import sys
    sys.exit(pytest.main([__file__, "-v"]))