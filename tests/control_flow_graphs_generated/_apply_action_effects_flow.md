# Control Flow: _apply_action_effects()

**Method:** `_apply_action_effects()`
**Lines:** 213-231
**Parameters:** action
**Control Flow Elements:** 2
**Cyclomatic Complexity:** 3

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_apply_action_effects()"])
  N1{"<b>IF</b><br/>Line 214<br/>if action < ACTION_H_BASE:"}
  N0 --> N1
  N2["return"]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 218<br/>if action < ACTION_V_BASE:"}
  N4 --> N5
  N6["idx = ...; wall_grid_size = ..."]
  N5 -->|true| N6
  N7["pass"]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9(["<b>END</b><br/>Return"])
  N8 --> N9

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
  - Line 214: if action < ACTION_H_BASE:
  - Line 218: if action < ACTION_V_BASE: