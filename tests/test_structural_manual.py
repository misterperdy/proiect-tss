import os
import sys

import pytest


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Quoridor_Class import BOARD_SIZE, QuoridorEnv

# ================== STRUCTURAL TEST CASES ==================
# Contains Statement Coverage, Branch Coverage, Condition Coverage, Path Coverage

@pytest.fixture
def env():
    """Provides a fresh instance of the real Quoridor environment for each test."""
    return QuoridorEnv()

def test_start_is_target(env):
    """
    Branch coverage: `if sr == target_row` evaluates to True.
    Guarantees early exit with True.
    """
    # Start on row 8, target is row 8
    assert env._has_path_with_temp(start=(8, 4), target_row=8) == True

def test_path_found_going_up(env):
    """
    Branch coverage: `if r > 0` and `if r - 1 == target_row` evaluate to True.
    Simulates a valid UP move that immediately finds the target row.
    """
    # Start on row 1, target is row 0. Path is clear by default.
    assert env._has_path_with_temp(start=(1, 4), target_row=0) == True

def test_path_found_going_down(env):
    """
    Branch coverage: `if r < BOARD_SIZE - 1` and `if r + 1 == target_row` evaluate to True.
    Simulates a valid DOWN move that immediately finds the target row.
    """
    # Start on row 7, target is row 8. Path is clear by default.
    assert env._has_path_with_temp(start=(7, 4), target_row=8) == True

def test_full_exploration_and_return_false(env):
    """
    Global branch coverage: evaluates `while q:` until False and reaches `return False`.
    We completely block a row using the real NumPy array to force the queue to empty.
    """
    # Block row 3 completely with horizontal walls
    # This prevents a pawn starting at row 4 from ever reaching row 0
    for c in range(BOARD_SIZE - 1):
        env.walls_h[3, c] = 1
    
    assert env._has_path_with_temp(start=(4, 4), target_row=0) == False

def test_visited_and_blocked_conditions(env):
    """
    Condition coverage: Tests the `not visited[ni]` and `not self._blocked_with_temp` conditions.
    Also covers enqueue moves for Left (`if c > 0`) and Right (`if c < BOARD_SIZE - 1`).
    """
    # Place a single horizontal wall directly above the pawn
    # Pawn is at (4,4), wall at horizontal grid [3, 4] blocks upward movement to (3,4)
    env.walls_h[3, 4] = 1
    
    # Starting from (4,4) with the target on row 0.
    # The BFS algorithm will fail to go straight Up.
    # It must test the Left and Right branches, mark them as visited, and go around the wall.
    assert env._has_path_with_temp(start=(4, 4), target_row=0) == True

def test_temporary_wall_logic(env):
    """
    Condition coverage: Specifically tests the integration of `temp_h` and `temp_v`
    arguments passed into `_blocked_with_temp`.
    """
    # Create a wall gap of exactly 1 space on row 3 for column 4.
    # A wall at c=0 blocks cols 0 & 1.
    # A wall at c=2 blocks cols 2 & 3.
    # A wall at c=5 blocks cols 5 & 6.
    # A wall at c=7 blocks cols 7 & 8.
    # This leaves ONLY column 4 open.
    env.walls_h[3, 0] = 1
    env.walls_h[3, 2] = 1
    env.walls_h[3, 5] = 1
    env.walls_h[3, 7] = 1
            
    # Normally, there is a path through the gap at column 4.
    assert env._has_path_with_temp(start=(4, 4), target_row=0) == True
    
    # Now, pass a temporary horizontal wall starting at [3, 3] or [3, 4].
    # Either will cover column 4 and seal the gap, without modifying `env.walls_h`.
    assert env._has_path_with_temp(start=(4, 4), target_row=0, temp_h=(3, 3)) == False