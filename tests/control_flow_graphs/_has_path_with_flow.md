# Control Flow: _has_path_with()

**Method:** `_has_path_with()`
**Lines:** 445-461
**Parameters:** start, target_row, h_walls, v_walls
**Control Flow Elements:** 4
**Cyclomatic Complexity:** 5

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_has_path_with()"])
  N1{"<b>WHILE</b><br/>Line 453<br/>while q:"}
  N0 --> N1
  N2["Loop<br/>Body"]
  N1 -->|true| N2
  N2 -."loop back".-> N1
  N3[["Exit Loop"]]
  N1 -->|false| N3
  N4{"<b>IF</b><br/>Line 455<br/>if r == target_row:"}
  N3 --> N4
  N5["return True"]
  N4 -->|true| N5
  N6["pass"]
  N4 -->|false| N6
  N7[["Converge"]]
  N5 --> N7
  N6 --> N7
  N8{"<b>FOR</b><br/>Line 457<br/>iter: for nr, nc in _pawn_legal_targets_from_p..."}
  N7 --> N8
  N9["Iteration"]
  N8 --> N9
  N9 -."next iteration".-> N8
  N10[["Loop Complete"]]
  N8 -->|done| N10
  N11{"<b>IF</b><br/>Line 458<br/>if (nr, nc) not in seen:"}
  N10 --> N11
  N12[".add(...); .append(...)"]
  N11 -->|true| N12
  N13["pass"]
  N11 -->|false| N13
  N14[["Converge"]]
  N12 --> N14
  N13 --> N14
  N15(["<b>END</b><br/>Return"])
  N14 --> N15

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

- **If statements:** 2
  - Line 455: if r == target_row:
  - Line 458: if (nr, nc) not in seen:
- **While loops:** 1
  - Line 453: while q:
- **For loops:** 1
  - Line 457: for nr, nc in _pawn_legal_targets_from_pos(self, player_i...