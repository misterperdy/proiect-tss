"""
tests/test_mutation_killers.py
==============================
Teste de tip strong mutation killers pentru mutanții supraviețuitori
identificați în Quoridor_Class.py.

Fiecare test respectă modelul RSP (Reachability → State Infection → Propagation)
al strong mutation testing:
  • Reachability   – instrucțiunea mutată este atinsă în execuție.
  • State Infection – starea programului diferă imediat după instrucțiunea mutată.
  • Propagation   – diferența de stare se observă în ieșirea finală a metodei.
"""

import os
import sys

import pytest


sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from Quoridor_Class import BOARD_SIZE, QuoridorEnv


@pytest.fixture
def env():
    """Fresh Quoridor environment for each mutation-killer test."""
    environment = QuoridorEnv()
    environment.reset()
    return environment


# ══════════════════════════════════════════════════════════════════════════════
# MTK-001
# ══════════════════════════════════════════════════════════════════════════════
def test_kills_mtk_001_has_path_left_branch_removed(env):
    """
    Mutant țintă (supraviețuitor, first-order):
    ─────────────────────────────────────────────
    ID:               MTK-001 / SURVIVED-Quoridor_Class.py-(l:433,c:16)
    Operator mutație: If_Statement → If_False
    Linia:            Quoridor_Class.py:433
    Modificare exactă:
        ORIGINAL: if not visited[ni] and not self._blocked_with_temp(r, c, r, c - 1, h_walls, v_walls, temp_h, temp_v):
        MUTANT:   if False:

    Efectul mutației:
        Ramura LEFT din BFS-ul de pathfinding este complet dezactivată —
        niciun nod aflat la stânga nodului curent nu mai este explorat.

    De ce a supraviețuit în suitele existente:
        Testele funcționale și structurale existente nu construiesc scenarii
        în care LEFT este *singura* ieșire dintr-un nod; există mereu și alte
        direcții disponibile, astfel că BFS-ul găsește traseul și fără LEFT.

    Demonstrarea neechivalenței (scenariul minim):
        Plasăm piesa la (1,1) și blocăm UP, DOWN, RIGHT cu pereți reali.
        Singura ieșire din (1,1) este LEFT → (1,0), de unde UP → (0,0) atinge
        row 0 (goal player 0).
          • Original → BFS explorează LEFT → găsește traseu → returnează True.
          • Mutant   → LEFT dezactivat (if False) → coada BFS se golește fără
                        a atinge row 0 → returnează False.
        Asertul final pică pe mutant și trece pe original: mutantul este omorât.
    """

    # ── Setup ────────────────────────────────────────────────────────────────
    # Tablă goală (niciun perete implicit).
    env.walls_h[:, :] = 0
    env.walls_v[:, :] = 0

    # Construim o "cușcă" în jurul lui (1,1) cu doar LEFT deschis:
    #
    #   row 0:  [   ] [   ] [   ]  ← goal pentru player 0
    #             |         |
    #           h[0,1]=1  (perete între row0 și row1, col 1)
    #             |
    #   row 1:  [(1,0)] ← [=(1,1)=] → BLOCAT (v[1,1]=1)
    #                           |
    #                        h[1,1]=1  (perete între row1 și row2, col 1)
    #
    env.walls_h[0, 1] = 1  # blochează (1,1) → (0,1)  [UP]
    env.walls_v[1, 1] = 1  # blochează (1,1) → (1,2)  [RIGHT]
    env.walls_h[1, 1] = 1  # blochează (1,1) → (2,1)  [DOWN]

    # ── Reachability + State Infection ───────────────────────────────────────
    # Verificăm că exact cele trei direcții blocate sunt blocate
    # și că LEFT (singura ieșire) este liberă.
    assert env._blocked_with_temp(1, 1, 0, 1, env.walls_h, env.walls_v) is True,  \
        "UP trebuie blocat"
    assert env._blocked_with_temp(1, 1, 1, 2, env.walls_h, env.walls_v) is True,  \
        "RIGHT trebuie blocat"
    assert env._blocked_with_temp(1, 1, 2, 1, env.walls_h, env.walls_v) is True,  \
        "DOWN trebuie blocat"
    assert env._blocked_with_temp(1, 1, 1, 0, env.walls_h, env.walls_v) is False, \
        "LEFT trebuie să fie liber — singura ieșire din (1,1)"

    # Confirmăm că fără LEFT, traseul dispare (perete temporar pe coridorul
    # (1,0)↔(1,1) prin temp_v=(0,0) blochează și coloana 0 la rândul 0-1).
    # Aceasta demonstrează că LEFT este *esențial*:
    assert env._has_path_with_temp((1, 1), 0, temp_v=(0, 0)) is False, \
        "Cu LEFT blocat temporar, nu există traseu → LEFT este esențial"

    # ── Propagation (asertul care omoară mutantul) ───────────────────────────
    # Pe original: BFS explorează LEFT → (1,0) → UP → (0,0) → row 0 → True.
    # Pe mutant:   LEFT dezactivat (if False) → BFS nu mai ajunge la row 0 → False.
    # Asertul pică pe mutant (False is True → AssertionError) și trece pe original.
    assert env._has_path_with_temp((1, 1), 0) is True, \
        "Original găsește traseu prin LEFT; mutantul (if False) nu îl găsește"


# ══════════════════════════════════════════════════════════════════════════════
# MTK-002
# ══════════════════════════════════════════════════════════════════════════════
def test_kills_mtk_002_neighbors_down_bound_check_relaxed(env):
    """
    Mutant țintă (supraviețuitor, first-order):
    ─────────────────────────────────────────────
    ID:               MTK-002 / SURVIVED-Quoridor_Class.py-(l:467,c:11)
    Operator mutație: Compare (< → <=)
    Linia:            Quoridor_Class.py:467
    Modificare exactă:
        ORIGINAL: if r < BOARD_SIZE - 1 and not self._blocked_with(r, c, r + 1, c, h_walls, v_walls):
        MUTANT:   if r <= BOARD_SIZE - 1 and not self._blocked_with(r, c, r + 1, c, h_walls, v_walls):

    Efectul mutației:
        La r = BOARD_SIZE - 1 (= 8, ultima linie a tablei), condiția originală
        este False (8 < 8 → False), deci vecinul de jos nu este generat.
        Pe mutant, condiția devine True (8 <= 8 → True), iar
        _blocked_with(8, c, 9, c, ...) este evaluat.
        Deoarece r1=8 nu satisface 0 <= r1 < wall_grid_size (8 < 8 → False),
        _blocked_with returnează False, și coordonata (9, c) — în afara tablei —
        este adăugată la lista de vecini.

    De ce a supraviețuit în suitele existente:
        Nu există niciun test care apelează direct _neighbors_with() cu r = 8
        (ultima linie a tablei). Testele de nivel mai înalt nu acoperă explicit
        acest caz limită.

    Demonstrarea neechivalenței (scenariul minim):
        Apelăm _neighbors_with(8, 4, ...) pe o tablă goală.
          • Original → {(7,4), (8,3), (8,5)}   (3 vecini valizi, toți în tablă).
          • Mutant   → {(7,4), (9,4), (8,3), (8,5)} (include coordonata ilegală (9,4)).
        Asertul set equality pică pe mutant: mutantul este omorât.
        Al doilea asert (bounds check) confirmă că (9,4) este în afara tablei.
    """

    # ── Setup ────────────────────────────────────────────────────────────────
    # Tablă goală — izolăm strict logica de limită inferioară.
    env.walls_h[:, :] = 0
    env.walls_v[:, :] = 0

    r = BOARD_SIZE - 1  # 8 — ultima linie validă a tablei
    c = 4               # coloana centrală (arbitrară, nu contează pentru bounds)

    # ── Reachability + State Infection ───────────────────────────────────────
    # Pe original, condiția de la linia 467 este False → vecinul de jos nu se adaugă.
    # Pe mutant, condiția devine True → _blocked_with(8,4,9,4,...) este evaluat.
    assert (r < BOARD_SIZE - 1) is False, \
        "Condiția originală (r < 8) este False la ultima linie → DOWN nu se adaugă"
    assert (r <= BOARD_SIZE - 1) is True, \
        "Condiția mutantului (r <= 8) este True la ultima linie → DOWN se încearcă"

    # _blocked_with(8,4,9,4,...): r1=8, r2=9, c1=c2=4.
    # Ramura 'r2 == r1+1': pentru cc in (3,4): 0<=r1<wall_grid_size → 0<=8<8 → False.
    # → returnează False, deci (9,4) este adăugat de mutant.
    assert env._blocked_with(r, c, r + 1, c, env.walls_h, env.walls_v) is False, \
        "_blocked_with nu blochează (8,4)→(9,4): bounds check eșuează silențios → False"

    # ── Propagation (asertul care omoară mutantul) ───────────────────────────
    neighbors = env._neighbors_with(r, c, env.walls_h, env.walls_v)

    # Pe original: [(7,4), (8,3), (8,5)] — exact 3 vecini valizi.
    # Pe mutant:   [(7,4), (9,4), (8,3), (8,5)] — (9,4) este în afara tablei.
    expected = {(BOARD_SIZE - 2, c), (r, c - 1), (r, c + 1)}
    assert set(neighbors) == expected, \
        "Mutantul adaugă (9,4) — coordonată ilegală — care nu trebuie să apară"

    # Verificare suplimentară: toți vecinii raportați de original sunt în tablă.
    assert all(0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE for nr, nc in neighbors), \
        "Toți vecinii trebuie să fie coordonate valide în interiorul tablei 9x9"
