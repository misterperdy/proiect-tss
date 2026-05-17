# Control Flow: undo()

**Method:** `undo()`
**Lines:** 152-171
**Parameters:** token
**Control Flow Elements:** 3
**Cyclomatic Complexity:** 4

```mermaid
flowchart TD

  N0(["<b>START</b><br/>undo()"])
  N1{"<b>IF</b><br/>Line 158<br/>if kind == "pawn":"}
  N0 --> N1
  N2["..."]
  N1 -->|true| N2
  N3["nested if ..."]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>IF</b><br/>Line 160<br/>elif kind == "hw":"}
  N4 --> N5
  N6["..."]
  N5 -->|true| N6
  N7["nested if ..."]
  N5 -->|false| N7
  N8[["Converge"]]
  N6 --> N8
  N7 --> N8
  N9{"<b>IF</b><br/>Line 166<br/>elif kind == "vw":"}
  N8 --> N9
  N10["..."]
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
  - Line 158: if kind == "pawn":
  - Line 160: elif kind == "hw":
  - Line 166: elif kind == "vw":