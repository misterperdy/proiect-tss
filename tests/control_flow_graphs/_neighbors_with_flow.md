# Control Flow: _neighbors_with()

**Method:** `_neighbors_with()`
**Lines:** 463-473
**Parameters:** r, c, h_walls, v_walls
**Control Flow Elements:** 4
**Cyclomatic Complexity:** 5

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_neighbors_with()"])
  N1{"<b>IF</b><br/>Line 465<br/>if r > 0 and not self._blocked_with(r, c..."}
  N0 --> N1
  N2[".append(...)"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 467<br/>if r < BOARD_SIZE - 1 and not self._bloc..."}
  N4 --> N5
  N6[".append(...)"]
  N5 -->|true| N6
  N7["pass"]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 469<br/>if c > 0 and not self._blocked_with(r, c..."}
  N8 --> N9
  N10[".append(...)"]
  N9 -->|true| N10
  N11["pass"]
  N9 -->|false| N11
  N12[["Converge"]]
  N10 --> N12
  N11 --> N12
  N13{"<b>IF</b><br/>Line 471<br/>if c < BOARD_SIZE - 1 and not self._bloc..."}
  N12 --> N13
  N14[".append(...)"]
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
  - Line 465: if r > 0 and not self._blocked_with(r, c, r - 1, c, h_wal...
  - Line 467: if r < BOARD_SIZE - 1 and not self._blocked_with(r, c, r ...
  - Line 469: if c > 0 and not self._blocked_with(r, c, r, c - 1, h_wal...
  - Line 471: if c < BOARD_SIZE - 1 and not self._blocked_with(r, c, r,...