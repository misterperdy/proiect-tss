import numpy as np
from collections import deque



BOARD_SIZE = 9
MAX_WALLS = 10

NUM_PAWN_ACTIONS = BOARD_SIZE * BOARD_SIZE
ACTION_PAWN_BASE = 0
NUM_H_WALLS = (BOARD_SIZE - 1) * (BOARD_SIZE - 1)
ACTION_H_BASE = NUM_PAWN_ACTIONS
NUM_V_WALLS = (BOARD_SIZE - 1) * (BOARD_SIZE - 1)
ACTION_V_BASE = ACTION_H_BASE + NUM_H_WALLS
NUM_ACTIONS = ACTION_V_BASE + NUM_V_WALLS


class QuoridorEnv:
    def __init__(self):
        self.reset()

    def clone(self):
        e = QuoridorEnv()
        e.pawns = list(self.pawns)
        e.walls_h = self.walls_h.copy()
        e.walls_v = self.walls_v.copy()
        e.walls_left = list(self.walls_left)
        e.player = self.player
        e.done = self.done
        e.winner = self.winner
        return e

    def reset(self, walls_left=None):
        self.pawns = [(BOARD_SIZE - 1, BOARD_SIZE // 2), (0, BOARD_SIZE // 2)]
        wall_grid_size = BOARD_SIZE - 1
        self.walls_h = np.zeros((wall_grid_size, wall_grid_size), dtype=np.int8)
        self.walls_v = np.zeros((wall_grid_size, wall_grid_size), dtype=np.int8)
        self.walls_left = list(walls_left) if walls_left else [MAX_WALLS, MAX_WALLS]
        self.player = 0
        self.done = False
        self.winner = None
        self._path_cache = {}
        self._walls_sig = None
        self._walls_sig_dirty = True
        self.walls_h_owner = np.full((wall_grid_size, wall_grid_size), -1, dtype=np.int8)
        self.walls_v_owner = np.full((wall_grid_size, wall_grid_size), -1, dtype=np.int8)
        self._position_history = {}
        return self.encode()

    def _get_walls_sig(self):
        """
        Fast, cached signature for current wall grids.
        Only depends on wall placement (not pawns, turn, or walls_left).
        """
        if self._walls_sig_dirty or self._walls_sig is None:
            self._walls_sig = (hash(self.walls_h.tobytes()), hash(self.walls_v.tobytes()))
            self._walls_sig_dirty = False
        return self._walls_sig

    def encode(self):
        try:
            from .state_encoder import encode_state_canonical
        except ImportError:
            from state_encoder import encode_state_canonical
        return encode_state_canonical(self)

    def observe(self):
        return {
            "pawns": self.pawns,
            "walls_h": self.walls_h,
            "walls_v": self.walls_v,
            "walls_left": self.walls_left,
            "player": self.player
        }

    

    def _position_key(self):
        wh, wv = self._get_walls_sig()
        return (tuple(self.pawns[0]), tuple(self.pawns[1]),
                wh, wv,
                tuple(self.walls_left), self.player)

    def step(self, action):
        if self.done:
            raise RuntimeError("Game already finished.")
        if not self.is_legal(action):
            self.done = True
            self.winner = self.player ^ 1
            return self.encode(), -1.0, True, {"illegal": True}

        self._apply_action_effects(action)
        last = self.player
        if self._reached_goal(last):
            self.done = True
            self.winner = last
        if not self.done:
            self.player ^= 1
        
        if not self.done:
            pos_key = self._position_key()
            self._position_history[pos_key] = self._position_history.get(pos_key, 0) + 1
            if self._position_history[pos_key] >= 3:
                self.done = True
                self.winner = None

        obs = self.encode()
        reward = 0.0
        if self.done:
            if self.winner is not None:
                reward = 1.0 if self.winner == last else -1.0
        return obs, reward, self.done, {}

    def apply(self, action):
        token = {"player": self.player, "done": self.done, "winner": self.winner,
                 "kind": None, "payload": None, "action": action}

        if action < ACTION_H_BASE:
            tr, tc = divmod(action, BOARD_SIZE)
            token["kind"] = "pawn"
            token["payload"] = self.pawns[self.player]
            self.pawns[self.player] = (tr, tc)
        elif action < ACTION_V_BASE:
            idx = action - ACTION_H_BASE
            wall_grid_size = BOARD_SIZE - 1
            wr, wc = divmod(idx, wall_grid_size)
            token["kind"] = "hw"
            token["payload"] = (wr, wc, self.player, self.walls_left[self.player], int(self.walls_h_owner[wr, wc]))
            self.walls_h[wr, wc] = 1
            self.walls_h_owner[wr, wc] = self.player
            self.walls_left[self.player] -= 1
            self._walls_sig_dirty = True
        else:
            idx = action - ACTION_V_BASE
            wall_grid_size = BOARD_SIZE - 1
            wr, wc = divmod(idx, wall_grid_size)
            token["kind"] = "vw"
            token["payload"] = (wr, wc, self.player, self.walls_left[self.player], int(self.walls_v_owner[wr, wc]))
            self.walls_v[wr, wc] = 1
            self.walls_v_owner[wr, wc] = self.player
            self.walls_left[self.player] -= 1
            self._walls_sig_dirty = True

        last = self.player
        if self._reached_goal(last):
            self.done = True
            self.winner = last
        if not self.done:
            self.player ^= 1
        return token

    def undo(self, token):
        self.player = token["player"]
        self.done = token["done"]
        self.winner = token["winner"]

        kind = token["kind"]
        if kind == "pawn":
            self.pawns[self.player] = token["payload"]
        elif kind == "hw":
            wr, wc, pl, prev_wl, prev_owner = token["payload"]
            self.walls_h[wr, wc] = 0
            self.walls_h_owner[wr, wc] = prev_owner
            self.walls_left[pl] = prev_wl
            self._walls_sig_dirty = True
        elif kind == "vw":
            wr, wc, pl, prev_wl, prev_owner = token["payload"]
            self.walls_v[wr, wc] = 0
            self.walls_v_owner[wr, wc] = prev_owner
            self.walls_left[pl] = prev_wl
            self._walls_sig_dirty = True

    def legal_actions(self):
        if self.done:
            return np.zeros(NUM_ACTIONS, dtype=np.float32)

        mask = np.zeros(NUM_ACTIONS, dtype=np.float32)
        cr, cc = self.pawns[self.player]
        opp = self.pawns[self.player ^ 1]
        for (tr, tc) in self._pawn_legal_targets(cr, cc, opp):
            mask[tr * BOARD_SIZE + tc] = 1.0

        if self.walls_left[self.player] > 0:
            wall_grid_size = BOARD_SIZE - 1
            for idx in range(NUM_H_WALLS):
                wr, wc = divmod(idx, wall_grid_size)
                if self._legal_h_wall(wr, wc):
                    mask[ACTION_H_BASE + idx] = 1.0
            for idx in range(NUM_V_WALLS):
                wr, wc = divmod(idx, wall_grid_size)
                if self._legal_v_wall(wr, wc):
                    mask[ACTION_V_BASE + idx] = 1.0
        return mask

    def is_legal(self, action):
        return self.legal_actions()[action] == 1.0

    def forward_pawn_actions(self):
        cr, cc = self.pawns[self.player]
        opp = self.pawns[self.player ^ 1]
        targets = self._pawn_legal_targets(cr, cc, opp)
        fwd_ids = []
        if self.player == 0:
            for tr, tc in targets:
                if tr < cr:
                    fwd_ids.append(tr * BOARD_SIZE + tc)
        else:
            for tr, tc in targets:
                if tr > cr:
                    fwd_ids.append(tr * BOARD_SIZE + tc)
        return fwd_ids

    def _apply_action_effects(self, action):
        if action < ACTION_H_BASE:
            tr, tc = divmod(action, BOARD_SIZE)
            self.pawns[self.player] = (tr, tc)
            return
        if action < ACTION_V_BASE:
            idx = action - ACTION_H_BASE
            wall_grid_size = BOARD_SIZE - 1
            wr, wc = divmod(idx, wall_grid_size)
            self.walls_h[wr, wc] = 1
            self.walls_h_owner[wr, wc] = self.player
            self.walls_left[self.player] -= 1
            return
        idx = action - ACTION_V_BASE
        wall_grid_size = BOARD_SIZE - 1
        wr, wc = divmod(idx, wall_grid_size)
        self.walls_v[wr, wc] = 1
        self.walls_v_owner[wr, wc] = self.player
        self.walls_left[self.player] -= 1

    def _pawn_legal_targets(self, cr, cc, opp):
        orr, occ = opp
        res = set()

        def can_cross(r1, c1, r2, c2):
            return not self._blocked(r1, c1, r2, c2)

        for dr, dc in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
            nr, nc = cr + dr, cc + dc
            if not (0 <= nr < BOARD_SIZE and 0 <= nc < BOARD_SIZE):
                continue
            if not can_cross(cr, cc, nr, nc):
                continue
            if (nr, nc) == (orr, occ):
                jr, jc = nr + dr, nc + dc
                if 0 <= jr < BOARD_SIZE and 0 <= jc < BOARD_SIZE and can_cross(nr, nc, jr, jc):
                    if (jr, jc) != (cr, cc):
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

    def _crosses_h(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        return 0 <= wr < wall_grid_size and 0 <= wc < wall_grid_size and self.walls_v[wr, wc] == 1

    def _crosses_v(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        return 0 <= wr < wall_grid_size and 0 <= wc < wall_grid_size and self.walls_h[wr, wc] == 1

    def _overlaps_h(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        if self.walls_h[wr, wc] == 1:
            return True
        if wc > 0 and self.walls_h[wr, wc - 1] == 1:
            return True
        if wc < wall_grid_size - 1 and self.walls_h[wr, wc + 1] == 1:
            return True
        return False

    def _overlaps_v(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        if self.walls_v[wr, wc] == 1:
            return True
        if wr > 0 and self.walls_v[wr - 1, wc] == 1:
            return True
        if wr < wall_grid_size - 1 and self.walls_v[wr + 1, wc] == 1:
            return True
        return False

    def _legal_h_wall(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        if not (0 <= wr < wall_grid_size and 0 <= wc < wall_grid_size):
            return False
        if self.walls_left[self.player] <= 0:
            return False
        if self._overlaps_h(wr, wc):
            return False
        if self._crosses_h(wr, wc):
            return False
        return self._check_paths_with_temp_wall(h=(wr, wc))

    def _legal_v_wall(self, wr, wc):
        wall_grid_size = BOARD_SIZE - 1
        if not (0 <= wr < wall_grid_size and 0 <= wc < wall_grid_size):
            return False
        if self.walls_left[self.player] <= 0:
            return False
        if self._overlaps_v(wr, wc):
            return False
        if self._crosses_v(wr, wc):
            return False
        return self._check_paths_with_temp_wall(v=(wr, wc))

    def _check_paths_with_temp_wall(self, h=None, v=None):
        """
        Check that both players retain a path to goal after a *temporary* wall.

        """
        walls_sig = self._get_walls_sig()
        key = (self.pawns[0], self.pawns[1], walls_sig, h, v)
        hit = self._path_cache.get(key)
        if hit is not None:
            return hit

        ok0 = self._has_path_with_temp(self.pawns[0], 0, temp_h=h, temp_v=v)
        ok1 = self._has_path_with_temp(self.pawns[1], BOARD_SIZE - 1, temp_h=h, temp_v=v)
        ok = ok0 and ok1
        self._path_cache[key] = ok
        return ok

    @staticmethod
    def _blocked_with_temp(r1, c1, r2, c2, h_walls, v_walls, temp_h=None, temp_v=None):
        """
        Like `_blocked_with`, but treats `temp_h` / `temp_v` (wall-grid coords)
        as present without copying wall arrays.
        """
        wall_grid_size = BOARD_SIZE - 1

        # Horizontal move: check vertical wall grid `v_walls`
        if r1 == r2:
            if c2 == c1 + 1:
                wc = c1
            elif c2 == c1 - 1:
                wc = c2
            else:
                return False

            rr = r1 - 1
            if 0 <= rr < wall_grid_size:
                if v_walls[rr, wc]:
                    return True
                if temp_v is not None and temp_v == (rr, wc):
                    return True
            rr = r1
            if 0 <= rr < wall_grid_size:
                if v_walls[rr, wc]:
                    return True
                if temp_v is not None and temp_v == (rr, wc):
                    return True
            return False

        # Vertical move: check horizontal wall grid `h_walls`
        if c1 == c2:
            if r2 == r1 + 1:
                wr = r1
            elif r2 == r1 - 1:
                wr = r2
            else:
                return False

            cc = c1 - 1
            if 0 <= cc < wall_grid_size:
                if h_walls[wr, cc]:
                    return True
                if temp_h is not None and temp_h == (wr, cc):
                    return True
            cc = c1
            if 0 <= cc < wall_grid_size:
                if h_walls[wr, cc]:
                    return True
                if temp_h is not None and temp_h == (wr, cc):
                    return True
            return False

        return False

    def _has_path_with_temp(self, start, target_row, temp_h=None, temp_v=None):
        """
        Fast path existence check with an optional temporary wall.
        """
        sr, sc = start
        if sr == target_row:
            return True

        h_walls = self.walls_h
        v_walls = self.walls_v

        # visited[r*BOARD_SIZE + c] in {0,1}
        visited = bytearray(BOARD_SIZE * BOARD_SIZE)
        start_i = sr * BOARD_SIZE + sc
        visited[start_i] = 1

        q = deque([start_i])
        while q:
            i = q.popleft()
            r = i // BOARD_SIZE
            c = i - r * BOARD_SIZE

            # Up
            if r > 0:
                ni = i - BOARD_SIZE
                if not visited[ni] and not self._blocked_with_temp(r, c, r - 1, c, h_walls, v_walls, temp_h, temp_v):
                    if r - 1 == target_row:
                        return True
                    visited[ni] = 1
                    q.append(ni)
            # Down
            if r < BOARD_SIZE - 1:
                ni = i + BOARD_SIZE
                if not visited[ni] and not self._blocked_with_temp(r, c, r + 1, c, h_walls, v_walls, temp_h, temp_v):
                    if r + 1 == target_row:
                        return True
                    visited[ni] = 1
                    q.append(ni)
            # Left
            if c > 0:
                ni = i - 1
                if not visited[ni] and not self._blocked_with_temp(r, c, r, c - 1, h_walls, v_walls, temp_h, temp_v):
                    visited[ni] = 1
                    q.append(ni)
            # Right
            if c < BOARD_SIZE - 1:
                ni = i + 1
                if not visited[ni] and not self._blocked_with_temp(r, c, r, c + 1, h_walls, v_walls, temp_h, temp_v):
                    visited[ni] = 1
                    q.append(ni)

        return False

    def _has_path_with(self, start, target_row, h_walls, v_walls):
        try:
            from .shortest import _pawn_legal_targets_from_pos
        except ImportError:
            from shortest import _pawn_legal_targets_from_pos
        player_idx = 0 if target_row == 0 else 1
        q = deque([start])
        seen = {start}
        while q:
            r, c = q.popleft()
            if r == target_row:
                return True
            for nr, nc in _pawn_legal_targets_from_pos(self, player_idx, r, c, h_walls, v_walls):
                if (nr, nc) not in seen:
                    seen.add((nr, nc))
                    q.append((nr, nc))
        return False

    def _neighbors_with(self, r, c, h_walls, v_walls):
        res = []
        if r > 0 and not self._blocked_with(r, c, r - 1, c, h_walls, v_walls):
            res.append((r - 1, c))
        if r < BOARD_SIZE - 1 and not self._blocked_with(r, c, r + 1, c, h_walls, v_walls):
            res.append((r + 1, c))
        if c > 0 and not self._blocked_with(r, c, r, c - 1, h_walls, v_walls):
            res.append((r, c - 1))
        if c < BOARD_SIZE - 1 and not self._blocked_with(r, c, r, c + 1, h_walls, v_walls):
            res.append((r, c + 1))
        return res

    def _blocked(self, r1, c1, r2, c2):
        return self._blocked_with(r1, c1, r2, c2, self.walls_h, self.walls_v)

    @staticmethod
    def _blocked_with(r1, c1, r2, c2, h_walls, v_walls):
        wall_grid_size = BOARD_SIZE - 1
        if r1 == r2:
            if c2 == c1 + 1:
                for rr in (r1 - 1, r1):
                    if 0 <= rr < wall_grid_size and 0 <= c1 < wall_grid_size and v_walls[rr, c1]:
                        return True
            elif c2 == c1 - 1:
                for rr in (r1 - 1, r1):
                    if 0 <= rr < wall_grid_size and 0 <= c2 < wall_grid_size and v_walls[rr, c2]:
                        return True
        if c1 == c2:
            if r2 == r1 + 1:
                for cc in (c1 - 1, c1):
                    if 0 <= r1 < wall_grid_size and 0 <= cc < wall_grid_size and h_walls[r1, cc]:
                        return True
            elif r2 == r1 - 1:
                for cc in (c1 - 1, c1):
                    if 0 <= r2 < wall_grid_size and 0 <= cc < wall_grid_size and h_walls[r2, cc]:
                        return True
        return False

    def _reached_goal(self, player_idx):
        r, _ = self.pawns[player_idx]
        if player_idx == 0:
            return r == 0
        else:
            return r == BOARD_SIZE - 1
