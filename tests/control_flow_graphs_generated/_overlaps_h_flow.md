# Control Flow: _overlaps_h()

**Method:** `_overlaps_h()`
**Lines:** 275-283
**Parameters:** wr, wc
**Control Flow Elements:** 3
**Cyclomatic Complexity:** 4

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_overlaps_h()"])
  N1{"<b>IF</b><br/>Line 277<br/>if self.walls_h[wr, wc] == 1:"}
  N0 --> N1
  N2["return True"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 279<br/>if wc > 0 and self.walls_h[wr, wc - 1] =..."}
  N4 --> N5
  N6["return True"]
  N5 -->|true| N6
  N7["pass"]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 281<br/>if wc < wall_grid_size - 1 and self.wall..."}
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
  - Line 277: if self.walls_h[wr, wc] == 1:
  - Line 279: if wc > 0 and self.walls_h[wr, wc - 1] == 1:
  - Line 281: if wc < wall_grid_size - 1 and self.walls_h[wr, wc + 1] =...