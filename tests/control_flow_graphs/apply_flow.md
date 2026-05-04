# Control Flow: apply()

**Method:** `apply()`
**Lines:** 114-150
**Parameters:** action
**Control Flow Elements:** 4
**Cyclomatic Complexity:** 5

```mermaid
flowchart TD

  N0(["<b>START</b><br/>apply()"])
  N1{"<b>IF</b><br/>Line 118<br/>if action < ACTION_H_BASE:"}
  N0 --> N1
  N2["..."]
  N1 -->|true| N2
  N3["nested if ..."]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 123<br/>elif action < ACTION_V_BASE:"}
  N4 --> N5
  N6["idx = ...; wall_grid_size = ..."]
  N5 -->|true| N6
  N7["idx = ...; wall_grid_size = ..."]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 145<br/>if self._reached_goal(last):"}
  N8 --> N9
  N10["..."]
  N9 -->|true| N10
  N11["pass"]
  N9 -->|false| N11
  N12[["Converge"]]
  N10 --> N12
  N11 --> N12
  N13{"<b>IF</b><br/>Line 148<br/>if not self.done:"}
  N12 --> N13
  N14["..."]
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
  - Line 118: if action < ACTION_H_BASE:
  - Line 123: elif action < ACTION_V_BASE:
  - Line 145: if self._reached_goal(last):
  - Line 148: if not self.done: