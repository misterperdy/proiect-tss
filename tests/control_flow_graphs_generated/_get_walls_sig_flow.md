# Control Flow: _get_walls_sig()

**Method:** `_get_walls_sig()`
**Lines:** 50-58
**Parameters:** self (implicit)
**Control Flow Elements:** 1
**Cyclomatic Complexity:** 2

```mermaid
flowchart TD

  N0(["<b>START</b><br/>_get_walls_sig()"])
  N1{"<b>IF</b><br/>Line 55<br/>if self._walls_sig_dirty or self._walls_..."}
  N0 --> N1
  N2["..."]
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
  - Line 55: if self._walls_sig_dirty or self._walls_sig is None: