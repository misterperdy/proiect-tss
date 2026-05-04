# Control Flow: _check_paths_with_temp_wall()

**Method:** `_check_paths_with_temp_wall()`
**Lines:** 319-334
**Parameters:** h, v
**Control Flow Elements:** 1
**Cyclomatic Complexity:** 2

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_check_paths_with_temp_wall()"])
  N1{"<b>IF</b><br/>Line 327<br/>if hit is not None:"}
  N0 --> N1
  N2["return hit"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5(["<b>END</b><br/>Return"])
  N4 --> N5

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

- **If statements:** 1
  - Line 327: if hit is not None: