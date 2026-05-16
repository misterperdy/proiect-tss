# Control Flow: forward_pawn_actions()

**Method:** `forward_pawn_actions()`
**Lines:** 198-211
**Parameters:** self (implicit)
**Control Flow Elements:** 5
**Cyclomatic Complexity:** 6

```mermaid
flowchart TD

  N0(["<b>START</b><br/>forward_pawn_actions()"])
  N1{"<b>IF</b><br/>Line 203<br/>if self.player == 0:"}
  N0 --> N1
  N2["..."]
  N1 -->|true| N2
  N3["..."]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>FOR</b><br/>Line 204<br/>iter: for tr, tc in targets:"}
  N4 --> N5
  N6["Iteration"]
  N5 --> N6
  N6 -."next iteration".-> N5
  N7[["Loop Complete"]]
  N5 -->|done| N7
  N8{"<b>IF</b><br/>Line 205<br/>if tr < cr:"}
  N7 --> N8
  N9[".append(...)"]
  N8 -->|true| N9
  N10["pass"]
  N8 -->|false| N10
  N11[["Converge"]]
  N9 --> N11
  N10 --> N11
  N12{"<b>FOR</b><br/>Line 208<br/>iter: for tr, tc in targets:"}
  N11 --> N12
  N13["Iteration"]
  N12 --> N13
  N13 -."next iteration".-> N12
  N14[["Loop Complete"]]
  N12 -->|done| N14
  N15{"<b>IF</b><br/>Line 209<br/>if tr > cr:"}
  N14 --> N15
  N16[".append(...)"]
  N15 -->|true| N16
  N17["pass"]
  N15 -->|false| N17
  N18[["Converge"]]
  N16 --> N18
  N17 --> N18
  N19(["<b>END</b><br/>Return"])
  N18 --> N19

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
  - Line 203: if self.player == 0:
  - Line 205: if tr < cr:
  - Line 209: if tr > cr:
- **For loops:** 2
  - Line 204: for tr, tc in targets:
  - Line 208: for tr, tc in targets: