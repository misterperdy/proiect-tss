import os
import sys

import pytest


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Quoridor_Class import ACTION_H_BASE, ACTION_V_BASE, BOARD_SIZE, QuoridorEnv


WALL_GRID_SIZE = BOARD_SIZE - 1


def h_action(wr, wc):
    # Map a horizontal wall grid position to the corresponding action id.
    return ACTION_H_BASE + wr * WALL_GRID_SIZE + wc


def v_action(wr, wc):
    # Map a vertical wall grid position to the corresponding action id.
    return ACTION_V_BASE + wr * WALL_GRID_SIZE + wc


def reset_walls(env):
    # Reset wall state directly so each test starts from a clean board.
    env.walls_h[:, :] = 0
    env.walls_v[:, :] = 0
    env.walls_h_owner[:, :] = -1
    env.walls_v_owner[:, :] = -1
    env._path_cache.clear()
    env._walls_sig_dirty = True


@pytest.fixture
def env():
    """Provide a fresh Quoridor environment for each structural test."""
    environment = QuoridorEnv()
    environment.reset()
    return environment


class TestWallPredicates:
    """Cover wall overlap and crossing predicates directly."""

    @pytest.mark.parametrize(
        "setup, expected",
        [
            (lambda e: e.walls_h.__setitem__((3, 3), 1), True),
            (lambda e: e.walls_h.__setitem__((3, 2), 1), True),
            (lambda e: e.walls_h.__setitem__((3, 4), 1), True),
            (lambda e: None, False),
        ],
    )
    def test_overlaps_h_cases(self, env, setup, expected):
        # Exercise the direct, left-side, right-side, and empty-board cases.
        reset_walls(env)
        setup(env)
        assert env._overlaps_h(3, 3) is expected

    @pytest.mark.parametrize(
        "setup, expected",
        [
            (lambda e: e.walls_v.__setitem__((3, 3), 1), True),
            (lambda e: e.walls_v.__setitem__((2, 3), 1), True),
            (lambda e: e.walls_v.__setitem__((4, 3), 1), True),
            (lambda e: None, False),
        ],
    )
    def test_overlaps_v_cases(self, env, setup, expected):
        # Exercise the direct, upper, lower, and empty-board cases.
        reset_walls(env)
        setup(env)
        assert env._overlaps_v(3, 3) is expected

    @pytest.mark.parametrize(
        "setup, expected_h, expected_v",
        [
            (lambda e: e.walls_v.__setitem__((3, 3), 1), True, False),
            (lambda e: e.walls_h.__setitem__((3, 3), 1), False, True),
            (lambda e: None, False, False),
        ],
    )
    def test_crosses_cases(self, env, setup, expected_h, expected_v):
        # Check both perpendicular crossing predicates for the same location.
        reset_walls(env)
        setup(env)
        assert bool(env._crosses_h(3, 3)) is expected_h
        assert bool(env._crosses_v(3, 3)) is expected_v


class TestBlockedMovement:
    """Exercise the movement-blocking helper with wall and no-wall paths."""

    @pytest.mark.parametrize(
        "r1, c1, r2, c2, setup, expected",
        [
            (4, 4, 4, 5, lambda e: e.walls_v.__setitem__((3, 4), 1), True),
            (4, 4, 4, 5, lambda e: e.walls_v.__setitem__((4, 4), 1), True),
            (4, 5, 4, 4, lambda e: e.walls_v.__setitem__((3, 4), 1), True),
            (4, 5, 4, 4, lambda e: e.walls_v.__setitem__((4, 4), 1), True),
            (4, 4, 5, 4, lambda e: e.walls_h.__setitem__((4, 3), 1), True),
            (4, 4, 5, 4, lambda e: e.walls_h.__setitem__((4, 4), 1), True),
            (5, 4, 4, 4, lambda e: e.walls_h.__setitem__((4, 3), 1), True),
            (5, 4, 4, 4, lambda e: e.walls_h.__setitem__((4, 4), 1), True),
            (4, 4, 5, 5, lambda e: None, False),
        ],
    )
    def test_blocked_with_cases(self, env, r1, c1, r2, c2, setup, expected):
        # Cover horizontal and vertical movement, plus a clear diagonal reject.
        reset_walls(env)
        setup(env)
        assert QuoridorEnv._blocked_with(r1, c1, r2, c2, env.walls_h, env.walls_v) is expected

    @pytest.mark.parametrize(
        "temp_h, temp_v, r1, c1, r2, c2, expected",
        [
            ((4, 4), None, 4, 4, 5, 4, True),
            (None, (4, 4), 4, 4, 4, 5, True),
            (None, None, 4, 4, 4, 5, False),
        ],
    )
    def test_blocked_with_temp_cases(self, env, temp_h, temp_v, r1, c1, r2, c2, expected):
        # Verify temporary walls are treated as present without mutating state.
        reset_walls(env)
        assert QuoridorEnv._blocked_with_temp(
            r1,
            c1,
            r2,
            c2,
            env.walls_h,
            env.walls_v,
            temp_h=temp_h,
            temp_v=temp_v,
        ) is expected


class TestLegalWalls:
    """Cover the top-level legality checks for horizontal and vertical walls."""

    def test_legal_h_wall_on_clean_board(self, env):
        # A simple valid placement should pass all guards.
        reset_walls(env)
        assert env._legal_h_wall(3, 3) is True

    def test_legal_h_wall_invalid_bounds(self, env):
        # Invalid coordinates must be rejected before any state checks run.
        reset_walls(env)
        assert env._legal_h_wall(-1, 3) is False
        assert env._legal_h_wall(3, 8) is False

    def test_legal_h_wall_no_walls_left(self, env):
        # Exhausted inventory should short-circuit the legality decision.
        reset_walls(env)
        env.walls_left[env.player] = 0
        assert env._legal_h_wall(3, 3) is False

    def test_legal_h_wall_overlap_and_crossing(self, env):
        # A same-axis overlap and a perpendicular crossing are both illegal.
        reset_walls(env)
        env.walls_h[3, 3] = 1
        assert env._legal_h_wall(3, 3) is False

        reset_walls(env)
        env.walls_v[3, 3] = 1
        assert env._legal_h_wall(3, 3) is False

    def test_legal_h_wall_blocks_path(self, env):
        # This placement closes the last remaining path to the goal.
        reset_walls(env)
        env.walls_v[7, 2] = 1
        env.walls_v[7, 4] = 1
        env._walls_sig_dirty = True
        assert env._legal_h_wall(7, 3) is False

    def test_legal_v_wall_on_clean_board(self, env):
        # Mirror the valid horizontal case for vertical walls.
        reset_walls(env)
        assert env._legal_v_wall(3, 3) is True

    def test_legal_v_wall_invalid_bounds(self, env):
        # Vertical wall coordinates use the same board limits.
        reset_walls(env)
        assert env._legal_v_wall(8, 3) is False
        assert env._legal_v_wall(3, -1) is False

    def test_legal_v_wall_no_walls_left(self, env):
        # The inventory guard should behave the same for both orientations.
        reset_walls(env)
        env.walls_left[env.player] = 0
        assert env._legal_v_wall(3, 3) is False

    def test_legal_v_wall_overlap_and_crossing(self, env):
        # A vertical overlap and a horizontal crossing are both rejected.
        reset_walls(env)
        env.walls_v[3, 3] = 1
        assert env._legal_v_wall(3, 3) is False

        reset_walls(env)
        env.walls_h[3, 3] = 1
        assert env._legal_v_wall(3, 3) is False

    def test_legal_v_wall_keeps_paths_on_clean_board(self, env):
        # Sanity check: the temporary path validator accepts a harmless move.
        reset_walls(env)
        assert env._check_paths_with_temp_wall(v=(3, 3)) is True


class TestApplyUndoWalls:
    """Verify wall application and rollback preserve board state."""

    def test_apply_and_undo_horizontal_wall(self, env):
        # Apply a horizontal wall, then undo it and check every changed field.
        reset_walls(env)
        token = env.apply(h_action(3, 3))

        assert env.walls_h[3, 3] == 1
        assert env.walls_h_owner[3, 3] == 0
        assert env.walls_left[0] == 9

        env.undo(token)

        assert env.walls_h[3, 3] == 0
        assert env.walls_h_owner[3, 3] == -1
        assert env.walls_left[0] == 10

    def test_apply_and_undo_vertical_wall(self, env):
        # Apply a vertical wall and confirm undo restores the original state.
        reset_walls(env)
        token = env.apply(v_action(3, 3))

        assert env.walls_v[3, 3] == 1
        assert env.walls_v_owner[3, 3] == 0
        assert env.walls_left[0] == 9

        env.undo(token)

        assert env.walls_v[3, 3] == 0
        assert env.walls_v_owner[3, 3] == -1
        assert env.walls_left[0] == 10


class TestPathAndIntegrationCoverage:
    """Fill structural gaps: path failures, API integration, and caching."""

    def test_has_path_with_temp_false_when_last_exit_is_closed(self, env):
        # Build a near-closure around player 0 and use a temporary wall to seal it.
        reset_walls(env)
        env.walls_v[7, 2] = 1
        env.walls_v[7, 4] = 1
        env._walls_sig_dirty = True

        assert env._has_path_with_temp(env.pawns[0], 0) is True
        assert env._has_path_with_temp(env.pawns[0], 0, temp_h=(7, 3)) is False

    def test_check_paths_with_temp_wall_false_when_blocking_all_routes(self, env):
        # Both legality helpers rely on this guard to reject full isolation.
        reset_walls(env)
        env.walls_v[7, 2] = 1
        env.walls_v[7, 4] = 1
        env._walls_sig_dirty = True

        assert env._check_paths_with_temp_wall(h=(7, 3)) is False

    def test_blocked_wrapper_uses_current_wall_state(self, env):
        # Cover the instance wrapper that delegates to _blocked_with.
        reset_walls(env)
        env.walls_v[3, 4] = 1
        env._walls_sig_dirty = True

        assert env._blocked(4, 4, 4, 5) is True
        assert env._blocked(4, 4, 5, 4) is False

    def test_legal_actions_and_is_legal_for_wall_moves(self, env):
        # Integration check: legality helper results must match action masks.
        reset_walls(env)
        action = h_action(3, 3)
        mask = env.legal_actions()
        assert mask[action] == 1.0
        assert bool(env.is_legal(action)) is True

        env.walls_h[3, 3] = 1
        env._walls_sig_dirty = True
        mask = env.legal_actions()
        assert mask[action] == 0.0
        assert bool(env.is_legal(action)) is False

    def test_legal_actions_disables_all_wall_actions_when_inventory_empty(self, env):
        # If no walls are left, the entire wall action ranges must be masked out.
        reset_walls(env)
        env.walls_left[env.player] = 0
        mask = env.legal_actions()

        assert mask[ACTION_H_BASE:ACTION_V_BASE].sum() == 0.0
        assert mask[ACTION_V_BASE:].sum() == 0.0

    def test_path_cache_reuses_and_recomputes_after_wall_change(self, env):
        # First call caches, repeated call reuses cache, wall change triggers new key.
        reset_walls(env)
        env._path_cache.clear()
        first = env._check_paths_with_temp_wall(h=(3, 3))
        size_after_first = len(env._path_cache)
        second = env._check_paths_with_temp_wall(h=(3, 3))
        size_after_second = len(env._path_cache)

        assert first is True
        assert second is True
        assert size_after_first == 1
        assert size_after_second == 1

        env.apply(h_action(0, 0))
        third = env._check_paths_with_temp_wall(h=(3, 3))
        size_after_third = len(env._path_cache)

        assert third is True
        assert size_after_third == 2
