# Control Flow: _reached_goal()

**Method:** `_reached_goal()`
**Lines:** 501-506
**Parameters:** player_idx
**Control Flow Elements:** 1
**Cyclomatic Complexity:** 2

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_reached_goal()"])
  N1{"<b>IF</b><br/>Line 503<br/>if player_idx == 0:"}
  N0 --> N1
  N2["return ..."]
  N1 -->|true| N2
  N3["return ..."]
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
  - Line 503: if player_idx == 0: