# Control Flow: legal_actions()

**Method:** `legal_actions()`
**Lines:** 173-193
**Parameters:** self (implicit)
**Control Flow Elements:** 7
**Cyclomatic Complexity:** 8

```mermaid
flowchart TD

  N0(["<b>START</b><br/>legal_actions()"])
  N1{"<b>IF</b><br/>Line 174<br/>if self.done:"}
  N0 --> N1
  N2["return ..."]
  N1 -->|true| N2
  N3["pass"]
  N1 -->|false| N3
  N4[["Converge"]]
  N2 --> N4
  N3 --> N4
  N5{"<b>FOR</b><br/>Line 180<br/>iter: for (tr, tc) in self._pawn_legal_targets..."}
  N4 --> N5
  N6["Iteration"]
  N5 --> N6
  N6 -."next iteration".-> N5
  N7[["Loop Complete"]]
  N5 -->|done| N7
  N8{"<b>IF</b><br/>Line 183<br/>if self.walls_left[self.player] > 0:"}
  N7 --> N8
  N9["wall_grid_size = ..."]
  N8 -->|true| N9
  N10["pass"]
  N8 -->|false| N10
  N11[["Converge"]]
  N9 --> N11
  N10 --> N11
  N12{"<b>FOR</b><br/>Line 185<br/>iter: for idx in range(NUM_H_WALLS):"}
  N11 --> N12
  N13["Iteration"]
  N12 --> N13
  N13 -."next iteration".-> N12
  N14[["Loop Complete"]]
  N12 -->|done| N14
  N15{"<b>IF</b><br/>Line 187<br/>if self._legal_h_wall(wr, wc):"}
  N14 --> N15
  N16["..."]
  N15 -->|true| N16
  N17["pass"]
  N15 -->|false| N17
  N18[["Converge"]]
  N16 --> N18
  N17 --> N18
  N19{"<b>FOR</b><br/>Line 189<br/>iter: for idx in range(NUM_V_WALLS):"}
  N18 --> N19
  N20["Iteration"]
  N19 --> N20
  N20 -."next iteration".-> N19
  N21[["Loop Complete"]]
  N19 -->|done| N21
  N22{"<b>IF</b><br/>Line 191<br/>if self._legal_v_wall(wr, wc):"}
  N21 --> N22
  N23["..."]
  N22 -->|true| N23
  N24["pass"]
  N22 -->|false| N24
  N25[["Converge"]]
  N23 --> N25
  N24 --> N25
  N26(["<b>END</b><br/>Return"])
  N25 --> N26

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
  - Line 174: if self.done:
  - Line 183: if self.walls_left[self.player] > 0:
  - Line 187: if self._legal_h_wall(wr, wc):
  - Line 191: if self._legal_v_wall(wr, wc):
- **For loops:** 3
  - Line 180: for (tr, tc) in self._pawn_legal_targets(cr, cc, opp):
  - Line 185: for idx in range(NUM_H_WALLS):
  - Line 189: for idx in range(NUM_V_WALLS):