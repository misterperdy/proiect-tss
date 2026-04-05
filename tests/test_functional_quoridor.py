"""
===================================================================================
QUORIDOR GAME: FUNCTIONAL TESTING SUITE (BLACK-BOX TESTING)
===================================================================================

CONTEXT & PURPOSE:
------------------
Welcome to the functional testing suite for the Quoridor game! 
If you are new to software testing, think of "Functional Testing" (specifically 
"Black-Box testing") as checking whether a car works properly by just driving it, 
without opening the hood to see how the engine is built. We provide certain inputs 
(like turning the steering wheel) and we expect a specific output (the car turns).

In our case, the "car" is the game logic (specifically the `QuoridorEnv` class), 
and we are testing if the game correctly allows or denies a player's attempt to 
place a wall on the board.

KEY TESTING CONCEPTS USED HERE:
-------------------------------
1. EQUIVALENCE PARTITIONING (EP): 
   Imagine a rule saying "Only ages 18 to 65 can enter". Instead of testing every 
   single age (18, 19, 20... 65), we divide all possible ages into general "classes" 
   (or partitions) that behave the same way:
   - Too young: ages 0 to 17 (e.g., test with age 10)
   - Valid: ages 18 to 65 (e.g., test with age 30)
   - Too old: ages 66+ (e.g., test with age 70)
   By testing just one number from each group, we save time and still confidently 
   prove the rule works. In this code, we partition inputs like "row number", 
   "column number", and "walls left in inventory".

2. BOUNDARY VALUE ANALYSIS (BVA):
   Programmers often make mistakes at the exact edges (boundaries) of limits. 
   Using the age example above, a programmer might mistakenly write `age > 18` 
   instead of `age >= 18`. To catch this, we combine BVA with EP by specifically 
   testing exactly on the boundary edges: 17, 18, 65, and 66.
   In this code, a valid wall row is between 0 and 7. To catch boundary bugs, 
   we won't just test row 3 (middle), we will specifically test row 0, row 7 
   (valid boundaries) and row -1, row 8 (invalid boundaries).

WHAT THIS CODE ACTUALLY DOES:
-----------------------------
This script runs a series of automated scenarios (called "test cases") using a 
popular tool called `pytest`. 
- `_overlaps_h`: We test if the game successfully detects when a player tries 
  to build a wall on top of another existing wall. (Using Equivalence Partitioning)
- `_legal_h_wall`: We test the core game rules for building horizontal walls. We 
  push the game to its limits by trying to build walls exactly on the board edges, 
  trying to build off the board entirely, trying to build with 0 walls left, and 
  trying to illegally trap a player so they can't reach the finish line. 
  (Using Equivalence Partitioning + Boundary Value Analysis)
===================================================================================
"""

import sys
import os
import pytest

# Add the parent directory to the sys.path so we can import Quoridor_Class.
# This ensures that tests can be run regardless of the current working directory.
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Quoridor_Class import QuoridorEnv


@pytest.fixture
def env():
    """
    Fixture to provide a clean Quoridor environment for each test.
    This guarantees that every test case acts on a fresh state.
    """
    environment = QuoridorEnv()
    environment.reset()
    return environment


class TestQuoridorOverlapsH:
    """
    Functional testing using Equivalence Partitioning (EP) for the method `_overlaps_h(self, wr, wc)`.
    
    This method checks if placing a horizontal wall at coordinates (wr, wc) overlaps 
    with an already existing horizontal wall on the board.
    
    Equivalence Classes based on the board state (input grid):
    - S_1: A horizontal wall exactly at (wr, wc) (direct overlap). [Expected Output -> True]
    - S_2: A horizontal wall directly to the left, at (wr, wc - 1) (left side overlap). [Expected Output -> True]
    - S_3: A horizontal wall directly to the right, at (wr, wc + 1) (right side overlap). [Expected Output -> True]
    - S_4: No adjacent horizontal walls in the immediate vicinity. [Expected Output -> False]
    """

    def test_ep_s1_direct_overlap(self, env):
        # Setup specific state for Equivalence Class S_1
        # Place a horizontal wall exactly at (3, 3)
        env.walls_h[3, 3] = 1
        
        # Test class S_1: The cell (3, 3) overlaps directly with the placed wall
        assert env._overlaps_h(3, 3) is True, "EP Class S_1 Failed: Expected True for direct overlap"

    def test_ep_s2_left_overlap(self, env):
        # Setup specific state for Equivalence Class S_2
        # Place a horizontal wall to the left at (3, 2)
        env.walls_h[3, 2] = 1
        
        # Test class S_2: The cell (3, 3) overlaps with the right side of the wall on its left
        assert env._overlaps_h(3, 3) is True, "EP Class S_2 Failed: Expected True for left overlap"

    def test_ep_s3_right_overlap(self, env):
        # Setup specific state for Equivalence Class S_3
        # Place a horizontal wall to the right at (3, 4)
        env.walls_h[3, 4] = 1
        
        # Test class S_3: The cell (3, 3) overlaps with the left side of the wall on its right
        assert env._overlaps_h(3, 3) is True, "EP Class S_3 Failed: Expected True for right overlap"

    def test_ep_s4_no_overlap(self, env):
        # Setup specific state for Equivalence Class S_4
        # Board is empty, no surrounding walls are placed
        env.walls_h[:, :] = 0
        
        # Test class S_4: The cell (3, 3) has no overlapping adjacent horizontal walls
        assert env._overlaps_h(3, 3) is False, "EP Class S_4 Failed: Expected False when there are no surrounding walls"


class TestQuoridorLegalHWall:
    """
    Functional testing using Equivalence Partitioning (EP) AND Boundary Value Analysis (BVA) 
    for the method `_legal_h_wall(self, wr, wc)`.
    
    Valid domain limits:
    - wr (row): 0 to 7
    - wc (col): 0 to 7
    - walls_left: 1 to 10
    
    Instead of testing random valid values, BVA dictates we test the extreme valid edges.
    Similarly, we use the immediate extreme invalid edges (-1, 8, 0) as representatives 
    for the invalid partitions.
    
    Equivalence & Boundary Classes:
    - VALID BOUNDARIES (BVA subsets of Valid EP Class):
        - BVA_1: Top-Left edge of the board with lowest valid wall count. (wr=0, wc=0, walls=1)
        - BVA_2: Top-Right edge of the board with highest valid wall count. (wr=0, wc=7, walls=10)
        - BVA_3: Bottom-Left edge of the board with lowest valid wall count. (wr=7, wc=0, walls=1)
        - BVA_4: Bottom-Right edge of the board with highest valid wall count. (wr=7, wc=7, walls=10)
    
    - INVALID BOUNDARIES & PARTITIONS:
        - BVA_C_2: Row boundary just below valid range (wr = -1). (Expected: False)
        - BVA_C_3: Row boundary just above valid range (wr = 8). (Expected: False)
        - BVA_C_4: Column boundary just below valid range (wc = -1). (Expected: False)
        - BVA_C_5: Column boundary just above valid range (wc = 8). (Expected: False)
        - BVA_C_6: Walls count boundary just below valid range (walls_left = 0). (Expected: False)
        - EP_C_7: State EP - horizontal wall overlap. (Expected: False)
        - EP_C_8: State EP - vertical wall crossing. (Expected: False)
        - EP_C_9: State EP - completely blocks victory paths. (Expected: False)
    """

    # ---------------------------------------------------------
    # VALID BOUNDARY VALUE ANALYSIS (BVA) TESTS (Replaces old C_1)
    # ---------------------------------------------------------

    def test_bva_1_top_left_edge(self, env):
        # Setup BVA_1: Extreme Top-Left edge.
        # Boundary parameters: wr = 0 (min valid), wc = 0 (min valid)
        # Using walls_left = 1 (min valid boundary)
        env.walls_left[env.player] = 1
        assert env._legal_h_wall(0, 0) is True, "BVA_1 Failed: Expected True at Top-Left board edge boundary"

    def test_bva_2_top_right_edge(self, env):
        # Setup BVA_2: Extreme Top-Right edge.
        # Boundary parameters: wr = 0 (min valid), wc = 7 (max valid)
        # Using walls_left = 10 (max valid boundary, default at reset)
        env.walls_left[env.player] = 10
        assert env._legal_h_wall(0, 7) is True, "BVA_2 Failed: Expected True at Top-Right board edge boundary"

    def test_bva_3_bottom_left_edge(self, env):
        # Setup BVA_3: Extreme Bottom-Left edge.
        # Boundary parameters: wr = 7 (max valid), wc = 0 (min valid)
        # Using walls_left = 1 (min valid boundary)
        env.walls_left[env.player] = 1
        assert env._legal_h_wall(7, 0) is True, "BVA_3 Failed: Expected True at Bottom-Left board edge boundary"

    def test_bva_4_bottom_right_edge(self, env):
        # Setup BVA_4: Extreme Bottom-Right edge.
        # Boundary parameters: wr = 7 (max valid), wc = 7 (max valid)
        # Using walls_left = 10 (max valid boundary, default at reset)
        env.walls_left[env.player] = 10
        assert env._legal_h_wall(7, 7) is True, "BVA_4 Failed: Expected True at Bottom-Right board edge boundary"

    # ---------------------------------------------------------
    # INVALID BOUNDARY VALUE ANALYSIS (BVA) TESTS
    # ---------------------------------------------------------

    def test_bva_c2_invalid_row_negative(self, env):
        # Setup class C_2 / BVA: Row boundary just outside valid range (-1)
        assert env._legal_h_wall(-1, 3) is False, "BVA_C_2 Failed: Expected False for negative row boundary (-1)"

    def test_bva_c3_invalid_row_too_large(self, env):
        # Setup class C_3 / BVA: Row boundary just outside valid range (8)
        assert env._legal_h_wall(8, 3) is False, "BVA_C_3 Failed: Expected False for excessive row boundary (8)"

    def test_bva_c4_invalid_col_negative(self, env):
        # Setup class C_4 / BVA: Column boundary just outside valid range (-1)
        assert env._legal_h_wall(3, -1) is False, "BVA_C_4 Failed: Expected False for negative col boundary (-1)"

    def test_bva_c5_invalid_col_too_large(self, env):
        # Setup class C_5 / BVA: Column boundary just outside valid range (8)
        assert env._legal_h_wall(3, 8) is False, "BVA_C_5 Failed: Expected False for excessive col boundary (8)"

    def test_bva_c6_no_walls_left(self, env):
        # Setup class C_6 / BVA: Walls inventory boundary just below valid (0)
        env.walls_left[env.player] = 0
        assert env._legal_h_wall(3, 3) is False, "BVA_C_6 Failed: Expected False since player has 0 walls left boundary"

    # ---------------------------------------------------------
    # INVALID EQUIVALENCE PARTITIONING (EP) STATE TESTS
    # ---------------------------------------------------------

    def test_ep_c7_horizontal_overlap(self, env):
        # Setup class C_7: An existing horizontal wall at (3, 3) creates a direct overlap
        env.walls_h[3, 3] = 1
        assert env._legal_h_wall(3, 3) is False, "EP_C_7 Failed: Expected False when there is a horizontal wall overlap"

    def test_ep_c8_vertical_crossing(self, env):
        # Setup class C_8: An existing vertical wall at (3, 3) creates a crossing / intersection
        env.walls_v[3, 3] = 1
        assert env._legal_h_wall(3, 3) is False, "EP_C_8 Failed: Expected False when it crosses an existing vertical wall"

    def test_ep_c9_blocks_path_to_goal(self, env):
        # Setup class C_9: Placing the wall restricts the only remaining path to the goal.
        
        # Player 0 starts at (8, 4) at the bottom edge and their goal is to reach row 0.
        # We will build vertical walls to the left and right of the player's vicinity
        # so that they can only escape the enclosure by moving upwards.
        
        # Place a vertical wall between col 2 and 3 (spanning across rows 7 and 8)
        env.walls_v[7, 2] = 1 
        
        # Place a vertical wall between col 4 and 5 (spanning across rows 7 and 8)
        env.walls_v[7, 4] = 1 

        # At this point, the player at (8, 4) can move left to (8, 3), but cannot move further to (8, 2).
        # The player cannot move right at all.
        # The only remaining escape paths require the player to move UP to either (7, 3) or (7, 4).
        
        # If we attempt to place a horizontal wall at (7, 3), it will cover columns 3 and 4,
        # effectively sealing the enclosure and blocking the upward movement completely.
        # This placement has no crossings or overlaps and is within bounds,
        # BUT it violates the rule that you cannot completely isolate a player from their goal.
        
        # We invalidate the internal path cache since we injected walls manually
        env._walls_sig_dirty = True
        
        # The pathfinding check _check_paths_with_temp_wall should detect the isolation and return False
        assert env._legal_h_wall(7, 3) is False, "EP_C_9 Failed: Expected False because this wall isolates user"
