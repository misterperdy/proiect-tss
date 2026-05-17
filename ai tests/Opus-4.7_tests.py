"""
Teste pentru QuoridorEnv (mediul Quoridor pentru Reinforcement Learning).

Ținta acestor teste sunt invarianții critici și locurile cu cea mai mare
probabilitate de a ascunde bug-uri:

  - Aspectul spațiului de acțiuni
  - Inversabilitatea apply / undo (critic pentru roll-out-uri MCTS)
  - Reguli de plasare a zidurilor (overlap, cross, blocare totală, buget)
  - Mișcările pionului (de bază, salt drept, salt diagonal, pătrat ocupat)
  - Detecția obiectivului / câștigătorului / alternanța turelor
  - Codificarea canonică a stării (rotația perspectivei pentru jucătorul 1)
  - Invalidarea cache-ului semnăturii zidurilor

Pot fi rulate cu:  python -m unittest test_quoridor_env.py
"""

import unittest
import numpy as np

from Quoridor_Class import (
    QuoridorEnv,
    BOARD_SIZE, MAX_WALLS, NUM_ACTIONS,
    NUM_PAWN_ACTIONS, NUM_H_WALLS, NUM_V_WALLS,
    ACTION_H_BASE, ACTION_V_BASE,
)
from state_encoder import (
    encode_state_canonical,
    policy_to_canonical, policy_from_canonical,
    mask_to_canonical,
)


# ----------------------------- helpers -----------------------------

def _pawn_action(r, c):
    return r * BOARD_SIZE + c

def _h_action(wr, wc):
    return ACTION_H_BASE + wr * (BOARD_SIZE - 1) + wc

def _v_action(wr, wc):
    return ACTION_V_BASE + wr * (BOARD_SIZE - 1) + wc


def _snapshot(env):
    """Captura completă a stării observabile (folosită pentru testul apply/undo)."""
    return (
        tuple(env.pawns),
        env.walls_h.copy(),
        env.walls_v.copy(),
        env.walls_h_owner.copy(),
        env.walls_v_owner.copy(),
        tuple(env.walls_left),
        env.player,
        env.done,
        env.winner,
    )


def _states_equal(s1, s2):
    return (
        s1[0] == s2[0]
        and np.array_equal(s1[1], s2[1])
        and np.array_equal(s1[2], s2[2])
        and np.array_equal(s1[3], s2[3])
        and np.array_equal(s1[4], s2[4])
        and s1[5] == s2[5]
        and s1[6] == s2[6]
        and s1[7] == s2[7]
        and s1[8] == s2[8]
    )


# ----------------------------- testele -----------------------------

class TestActionSpace(unittest.TestCase):
    """Constantele spațiului de acțiuni trebuie să partiționeze corect indecșii."""

    def test_partition_dimensions(self):
        self.assertEqual(NUM_PAWN_ACTIONS, BOARD_SIZE * BOARD_SIZE)
        self.assertEqual(NUM_H_WALLS, (BOARD_SIZE - 1) ** 2)
        self.assertEqual(NUM_V_WALLS, (BOARD_SIZE - 1) ** 2)
        self.assertEqual(NUM_ACTIONS, NUM_PAWN_ACTIONS + NUM_H_WALLS + NUM_V_WALLS)
        self.assertEqual(ACTION_H_BASE, NUM_PAWN_ACTIONS)
        self.assertEqual(ACTION_V_BASE, NUM_PAWN_ACTIONS + NUM_H_WALLS)


class TestInitialState(unittest.TestCase):
    """După reset(), starea trebuie să fie cea oficială de început."""

    def setUp(self):
        self.env = QuoridorEnv()

    def test_pawn_positions(self):
        self.assertEqual(self.env.pawns[0], (BOARD_SIZE - 1, BOARD_SIZE // 2))
        self.assertEqual(self.env.pawns[1], (0, BOARD_SIZE // 2))

    def test_walls_left_and_no_walls_placed(self):
        self.assertEqual(self.env.walls_left, [MAX_WALLS, MAX_WALLS])
        self.assertEqual(int(self.env.walls_h.sum()), 0)
        self.assertEqual(int(self.env.walls_v.sum()), 0)
        self.assertTrue((self.env.walls_h_owner == -1).all())
        self.assertTrue((self.env.walls_v_owner == -1).all())

    def test_turn_and_status(self):
        self.assertEqual(self.env.player, 0)
        self.assertFalse(self.env.done)
        self.assertIsNone(self.env.winner)

    def test_initial_legal_pawn_moves(self):
        """Pionul 0 din (8,4) are exact 3 mutări legale: sus, stânga, dreapta."""
        mask = self.env.legal_actions()
        pawn_legal_count = int(mask[:NUM_PAWN_ACTIONS].sum())
        self.assertEqual(pawn_legal_count, 3)
        self.assertEqual(mask[_pawn_action(7, 4)], 1.0)   # sus
        self.assertEqual(mask[_pawn_action(8, 3)], 1.0)   # stânga
        self.assertEqual(mask[_pawn_action(8, 5)], 1.0)   # dreapta
        self.assertEqual(mask[_pawn_action(8, 4)], 0.0)   # nu poate sta
        self.assertEqual(mask[_pawn_action(0, 4)], 0.0)   # destinație ocupată

    def test_reset_walls_left_override(self):
        self.env.reset(walls_left=[3, 5])
        self.assertEqual(self.env.walls_left, [3, 5])
        self.assertEqual(self.env.pawns[0], (BOARD_SIZE - 1, BOARD_SIZE // 2))


class TestApplyUndo(unittest.TestCase):
    """apply -> undo trebuie să fie un invers perfect (critic pentru MCTS)."""

    def test_pawn_move_roundtrip(self):
        env = QuoridorEnv()
        pre = _snapshot(env)
        env.undo(env.apply(_pawn_action(7, 4)))
        self.assertTrue(_states_equal(pre, _snapshot(env)))

    def test_h_wall_roundtrip(self):
        env = QuoridorEnv()
        pre = _snapshot(env)
        env.undo(env.apply(_h_action(3, 4)))
        self.assertTrue(_states_equal(pre, _snapshot(env)))

    def test_v_wall_roundtrip(self):
        env = QuoridorEnv()
        pre = _snapshot(env)
        env.undo(env.apply(_v_action(3, 4)))
        self.assertTrue(_states_equal(pre, _snapshot(env)))

    def test_long_random_sequence_full_unwind(self):
        """Aplică 50 de acțiuni legale aleatoare, apoi le derulează invers."""
        rng = np.random.default_rng(0)
        env = QuoridorEnv()
        initial = _snapshot(env)
        tokens = []
        for _ in range(50):
            if env.done:
                break
            legal = np.where(env.legal_actions() > 0)[0]
            if legal.size == 0:
                break
            tokens.append(env.apply(int(rng.choice(legal))))
        for tok in reversed(tokens):
            env.undo(tok)
        self.assertTrue(_states_equal(initial, _snapshot(env)))

    def test_winning_move_undo_restores_done_flag(self):
        """Mutarea câștigătoare setează done/winner; undo trebuie să le anuleze."""
        env = QuoridorEnv()
        env.pawns[0] = (1, 4)  # un pas de obiectiv
        tok = env.apply(_pawn_action(0, 4))
        self.assertTrue(env.done)
        self.assertEqual(env.winner, 0)
        # Turul NU se schimbă după mutarea câștigătoare.
        self.assertEqual(env.player, 0)
        env.undo(tok)
        self.assertFalse(env.done)
        self.assertIsNone(env.winner)
        self.assertEqual(env.player, 0)
        self.assertEqual(env.pawns[0], (1, 4))


class TestWallRules(unittest.TestCase):
    """Reguli de plasare a zidurilor: overlap, cross, buget, blocare drum."""

    def test_h_wall_overlap_is_rejected(self):
        env = QuoridorEnv()
        env.apply(_h_action(4, 4))
        env.player = 0  # forțăm întoarcerea la jucătorul 0 pentru a-i testa masca
        mask = env.legal_actions()
        # Zidurile orizontale adiacente împart o jumătate.
        self.assertEqual(mask[_h_action(4, 3)], 0.0)
        self.assertEqual(mask[_h_action(4, 5)], 0.0)
        # Plasarea în aceeași celulă - evident interzisă.
        self.assertEqual(mask[_h_action(4, 4)], 0.0)
        # Distanță >= 2 pe același rând - OK.
        self.assertEqual(mask[_h_action(4, 6)], 1.0)
        # Pe alt rând - OK.
        self.assertEqual(mask[_h_action(3, 4)], 1.0)

    def test_v_wall_overlap_is_rejected(self):
        env = QuoridorEnv()
        env.apply(_v_action(4, 4))
        env.player = 0
        mask = env.legal_actions()
        self.assertEqual(mask[_v_action(3, 4)], 0.0)
        self.assertEqual(mask[_v_action(5, 4)], 0.0)
        self.assertEqual(mask[_v_action(4, 4)], 0.0)
        # Pe aceeași coloană, dar la rând non-adiacent - OK.
        self.assertEqual(mask[_v_action(6, 4)], 1.0)

    def test_h_and_v_walls_cannot_cross(self):
        env = QuoridorEnv()
        env.apply(_h_action(4, 4))
        env.player = 0
        mask = env.legal_actions()
        # V-zid la aceeași intersecție (wr, wc) - se intersectează.
        self.assertEqual(mask[_v_action(4, 4)], 0.0)

    def test_no_walls_when_budget_zero(self):
        env = QuoridorEnv()
        env.walls_left[0] = 0
        mask = env.legal_actions()
        # Niciun zid legal.
        self.assertEqual(int(mask[ACTION_H_BASE:].sum()), 0)
        # Mutările pionului rămân disponibile.
        self.assertGreater(int(mask[:NUM_PAWN_ACTIONS].sum()), 0)

    def test_wall_actually_blocks_pawn(self):
        """Zid plasat -> mișcarea care îl traversează trebuie ilegală."""
        env = QuoridorEnv()
        # H-zid la (7,4) blochează (7,4)<->(8,4) și (7,5)<->(8,5).
        env.apply(_h_action(7, 4))
        # Jucătorul 1 mută orice e legal.
        m1 = env.legal_actions()
        env.apply(int(np.where(m1 > 0)[0][0]))
        # Acum jucătorul 0 nu mai poate urca la (7,4).
        mask = env.legal_actions()
        self.assertEqual(mask[_pawn_action(7, 4)], 0.0)
        # Dar mișcările laterale rămân legale.
        self.assertEqual(mask[_pawn_action(8, 3)], 1.0)
        self.assertEqual(mask[_pawn_action(8, 5)], 1.0)

    def test_wall_that_traps_opponent_is_rejected(self):
        """
        Plasarea unui zid care lasă oricare jucător fără drum spre obiectiv
        trebuie să fie ilegală - DAR doar din motivul de drum, nu overlap/cross.
        """
        env = QuoridorEnv()
        # Construim un capcan-de-colț pentru pionul 1.
        env.pawns[1] = (0, 0)
        env.walls_v[0, 0] = 1                 # blochează (0,0)<->(0,1) și (1,0)<->(1,1)
        env._walls_sig_dirty = True

        # Pre-condiție: pionul 1 are încă drum spre rândul 8 prin (1,0)->(2,0)->...
        self.assertTrue(env._has_path_with_temp(env.pawns[1], BOARD_SIZE - 1))

        # H-zidul la (1,0) ar bloca (1,0)<->(2,0): pionul 1 ar fi prins în
        # {(0,0),(1,0)} fără ieșire spre rândul 8.
        mask = env.legal_actions()
        self.assertEqual(
            mask[_h_action(1, 0)], 0.0,
            "Zidul care anulează drumul singular al adversarului trebuie să fie ilegal"
        )
        # Sanity: respingerea NU vine din overlap/cross/buget.
        self.assertFalse(env._overlaps_h(1, 0))
        self.assertFalse(env._crosses_h(1, 0))
        self.assertGreater(env.walls_left[0], 0)

    def test_wall_owner_is_recorded(self):
        env = QuoridorEnv()
        # Mutarea 1: jucătorul 0 pune un h-zid.
        env.apply(_h_action(3, 3))
        self.assertEqual(int(env.walls_h_owner[3, 3]), 0)
        # Mutarea 2: jucătorul 1 pune un v-zid.
        env.apply(_v_action(5, 5))
        self.assertEqual(int(env.walls_v_owner[5, 5]), 1)


class TestPawnMovement(unittest.TestCase):
    """Mișcările pionului, inclusiv salturile peste adversar."""

    def test_cannot_move_to_opponent_square(self):
        env = QuoridorEnv()
        env.pawns[0] = (4, 4)
        env.pawns[1] = (3, 4)  # direct deasupra
        mask = env.legal_actions()
        self.assertEqual(mask[_pawn_action(3, 4)], 0.0)

    def test_straight_jump_over_opponent(self):
        env = QuoridorEnv()
        env.pawns[0] = (4, 4)
        env.pawns[1] = (3, 4)
        mask = env.legal_actions()
        # (2,4) e ținta saltului drept.
        self.assertEqual(mask[_pawn_action(2, 4)], 1.0)
        # Când saltul drept e disponibil, diagonalele NU trebuie legale.
        self.assertEqual(mask[_pawn_action(3, 3)], 0.0)
        self.assertEqual(mask[_pawn_action(3, 5)], 0.0)

    def test_diagonal_jump_when_blocked_behind_opponent(self):
        env = QuoridorEnv()
        env.pawns[0] = (4, 4)
        env.pawns[1] = (3, 4)
        # H-zid între (2,4) și (3,4) -> blochează saltul drept.
        env.walls_h[2, 4] = 1
        env._walls_sig_dirty = True
        mask = env.legal_actions()
        # Saltul drept e blocat.
        self.assertEqual(mask[_pawn_action(2, 4)], 0.0)
        # Salturile diagonale (3,3) și (3,5) devin legale.
        self.assertEqual(mask[_pawn_action(3, 3)], 1.0)
        self.assertEqual(mask[_pawn_action(3, 5)], 1.0)

    def test_jump_fallback_at_board_edge(self):
        """
        Adversar lipit de marginea tablei -> saltul drept e OOB,
        așa că diagonalele trebuie să fie legale.
        """
        env = QuoridorEnv()
        env.pawns[0] = (1, 4)
        env.pawns[1] = (0, 4)  # rândul 0, salt drept ar fi (-1,4) - OOB
        mask = env.legal_actions()
        self.assertEqual(mask[_pawn_action(0, 3)], 1.0)
        self.assertEqual(mask[_pawn_action(0, 5)], 1.0)
        self.assertEqual(mask[_pawn_action(0, 4)], 0.0)  # pătrat ocupat


class TestGoalAndTurns(unittest.TestCase):
    """Detecția victoriei și alternanța turelor."""

    def test_player0_wins_at_row_0(self):
        env = QuoridorEnv()
        env.pawns[0] = (1, 4)
        env.apply(_pawn_action(0, 4))
        self.assertTrue(env.done)
        self.assertEqual(env.winner, 0)
        # Turul NU se schimbă - câștigătorul rămâne mover-ul.
        self.assertEqual(env.player, 0)

    def test_player1_wins_at_row_8(self):
        env = QuoridorEnv()
        env.pawns[1] = (BOARD_SIZE - 2, 4)
        env.player = 1
        env.apply(_pawn_action(BOARD_SIZE - 1, 4))
        self.assertTrue(env.done)
        self.assertEqual(env.winner, 1)
        self.assertEqual(env.player, 1)

    def test_turn_alternation_on_normal_moves(self):
        env = QuoridorEnv()
        self.assertEqual(env.player, 0)
        env.apply(_pawn_action(7, 4))
        self.assertEqual(env.player, 1)
        env.apply(_pawn_action(1, 4))
        self.assertEqual(env.player, 0)

    def test_no_legal_actions_when_done(self):
        env = QuoridorEnv()
        env.pawns[0] = (1, 4)
        env.apply(_pawn_action(0, 4))
        self.assertTrue(env.done)
        self.assertEqual(int(env.legal_actions().sum()), 0)


class TestStateEncoding(unittest.TestCase):
    """Codificarea canonică a stării: invariantă la perspectivă."""

    def test_initial_state_canonical_symmetry(self):
        """În poziția simetrică inițială, ambele perspective canonice coincid."""
        env = QuoridorEnv()
        enc_p0 = encode_state_canonical(env)
        env.player = 1
        enc_p1 = encode_state_canonical(env)
        np.testing.assert_array_equal(enc_p0, enc_p1)

    def test_canonical_pawn_planes_orientation(self):
        """Jucătorul curent e mereu la rândul 8 (jos), adversarul la rândul 0."""
        env = QuoridorEnv()

        enc = encode_state_canonical(env)  # jucătorul 0
        self.assertEqual(enc[0, BOARD_SIZE - 1, BOARD_SIZE // 2], 1.0)
        self.assertEqual(float(enc[0].sum()), 1.0)
        self.assertEqual(enc[1, 0, BOARD_SIZE // 2], 1.0)
        self.assertEqual(float(enc[1].sum()), 1.0)

        env.player = 1
        enc = encode_state_canonical(env)
        # După rotația 180°, pionul 1 (de la (0,4)) apare la (8,4).
        self.assertEqual(enc[0, BOARD_SIZE - 1, BOARD_SIZE // 2], 1.0)
        self.assertEqual(enc[1, 0, BOARD_SIZE // 2], 1.0)

    def test_encoding_has_expected_shape(self):
        env = QuoridorEnv()
        enc = encode_state_canonical(env)
        self.assertEqual(enc.shape, (7, BOARD_SIZE, BOARD_SIZE))

    def test_policy_roundtrip_under_canonicalization(self):
        rng = np.random.default_rng(7)
        pi = rng.random(NUM_ACTIONS).astype(np.float32)
        for player in (0, 1):
            pi_can = policy_to_canonical(pi, player)
            pi_back = policy_from_canonical(pi_can, player)
            np.testing.assert_allclose(pi_back, pi)

    def test_mask_canonical_preserves_legal_count(self):
        env = QuoridorEnv()
        mask = env.legal_actions()
        for player in (0, 1):
            mask_can = mask_to_canonical(mask, player)
            self.assertEqual(mask.sum(), mask_can.sum())


class TestWallsSignatureCache(unittest.TestCase):
    """Semnătura zidurilor (folosită pentru cache-ul drumurilor)
    trebuie să fie sensibilă DOAR la modificările de ziduri."""

    def test_sig_changes_after_wall_placement(self):
        env = QuoridorEnv()
        sig0 = env._get_walls_sig()
        env.apply(_h_action(3, 3))
        sig1 = env._get_walls_sig()
        self.assertNotEqual(sig0, sig1)

    def test_sig_restored_after_undo(self):
        env = QuoridorEnv()
        sig0 = env._get_walls_sig()
        tok = env.apply(_h_action(3, 3))
        env.undo(tok)
        sig1 = env._get_walls_sig()
        self.assertEqual(sig0, sig1)

    def test_sig_unchanged_after_pawn_move(self):
        env = QuoridorEnv()
        sig0 = env._get_walls_sig()
        env.apply(_pawn_action(7, 4))
        sig1 = env._get_walls_sig()
        self.assertEqual(sig0, sig1)


class TestLegalMaskConsistency(unittest.TestCase):
    """Orice acțiune marcată legală trebuie să fie aplicabilă & reversibilă."""

    def test_random_legal_actions_apply_and_undo_cleanly(self):
        rng = np.random.default_rng(1)
        env = QuoridorEnv()
        for _ in range(15):
            if env.done:
                break
            mask = env.legal_actions()
            legal = np.where(mask > 0)[0]
            self.assertGreater(legal.size, 0)
            # Spot-check: din cele legale, câteva trebuie să meargă apply/undo.
            for a in rng.choice(legal, size=min(5, legal.size), replace=False):
                pre = _snapshot(env)
                tok = env.apply(int(a))
                env.undo(tok)
                self.assertTrue(
                    _states_equal(pre, _snapshot(env)),
                    f"apply/undo nu a restabilit starea pentru acțiunea {int(a)}"
                )
            env.apply(int(rng.choice(legal)))


if __name__ == "__main__":
    unittest.main()
