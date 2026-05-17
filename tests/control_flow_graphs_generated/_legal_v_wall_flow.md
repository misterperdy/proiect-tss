# Control Flow: _legal_v_wall()

**Method:** `_legal_v_wall()`
**Lines:** 307-317
**Parameters:** wr, wc
**Control Flow Elements:** 4
**Cyclomatic Complexity:** 5

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_legal_v_wall()"])
  N1{"<b>IF</b><br/>Line 309<br/>if not (0 <= wr < wall_grid_size and 0 <..."}
  N0 --> N1
  N2["return False"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 311<br/>if self.walls_left[self.player] <= 0:"}
  N4 --> N5
  N6["return False"]
  N5 -->|true| N6
  N7["pass"]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 313<br/>if self._overlaps_v(wr, wc):"}
  N8 --> N9
  N10["return False"]
  N9 -->|true| N10
  N11["pass"]
  N9 -->|false| N11
  N12[["Converge"]]
  N10 --> N12
  N11 --> N12
  N13{"<b>IF</b><br/>Line 315<br/>if self._crosses_v(wr, wc):"}
  N12 --> N13
  N14["return False"]
  N13 -->|true| N14
  N15["pass"]
  N13 -->|false| N15
  N16[["Converge"]]
  N14 --> N16
  N15 --> N16
  N17(["<b>END</b><br/>Return"])
  N16 --> N17

```

## Legend

| Element | Description |
|---------|-------------|
| Round boxes | Entry/Exit points |
| Diamond | Decision point (if statement) |
| Rectangle | Loop or branch block |
| Double bracket | Convergence/merging point |
| Dotted line | Loop back edge |

## Control Flow Summary

- **If statements:** 4
  - Line 309: if not (0 <= wr < wall_grid_size and 0 <= wc < wall_grid_...
  - Line 311: if self.walls_left[self.player] <= 0:
  - Line 313: if self._overlaps_v(wr, wc):
  - Line 315: if self._crosses_v(wr, wc):