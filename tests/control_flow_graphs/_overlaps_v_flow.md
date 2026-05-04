# Control Flow: _overlaps_v()

**Method:** `_overlaps_v()`
**Lines:** 285-293
**Parameters:** wr, wc
**Control Flow Elements:** 3
**Cyclomatic Complexity:** 4

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_overlaps_v()"])
  N1{"<b>IF</b><br/>Line 287<br/>if self.walls_v[wr, wc] == 1:"}
  N0 --> N1
  N2["return True"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 289<br/>if wr > 0 and self.walls_v[wr - 1, wc] =..."}
  N4 --> N5
  N6["return True"]
  N5 -->|true| N6
  N7["pass"]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 291<br/>if wr < wall_grid_size - 1 and self.wall..."}
  N8 --> N9
  N10["return True"]
  N9 -->|true| N10
  N11["pass"]
  N9 -->|false| N11
  N12[["Converge"]]
  N10 --> N12
  N11 --> N12
  N13(["<b>END</b><br/>Return"])
  N12 --> N13

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

- **If statements:** 3
  - Line 287: if self.walls_v[wr, wc] == 1:
  - Line 289: if wr > 0 and self.walls_v[wr - 1, wc] == 1:
  - Line 291: if wr < wall_grid_size - 1 and self.walls_v[wr + 1, wc] =...