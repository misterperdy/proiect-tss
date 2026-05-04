# Recenzie LLM-as-a-Judge: GPT-5.4 vs. Opus-4.7 vs. Teste Scrise de Oameni
### Mediul de Reinforcement Learning pentru Quoridor

| | |
|---|---|
| **Data** | 2026-05-03 |
| **Judecător** | Claude Sonnet 4.6 |
| **Subiect** | `QuoridorEnv` — un mediu de joc Quoridor destinat Reinforcement Learning, implementat în `Quoridor_Class.py` (module ajutătoare: `shortest.py`, `state_encoder.py`) |

---

**Prompt-ul dat ambelor LLM-uri:**

> „Ești un inginer software. Ți s-a dat această clasă Python (împreună cu 2 scripturi ajutătoare). Știi dinainte că această clasă definește un mediu pentru jocul Quoridor, conceput special pentru Reinforcement Learning. Sarcina ta este să analizezi clasa și să scrii câteva teste eficiente și optime pentru a te asigura că mediul este pregătit pentru următoarea sa fază. Nu ești obligat să acoperiți întreaga clasă, dar testele pe care le scrii ar trebui să identifice componentele de bază ale clasei și potențialele sale vulnerabilități."
>

---

## 1. Prezentare generală a fiecărei suite

### GPT-5.4 (`GPT-5.4_tests.py`)
| Proprietate | Valoare |
|---|---|
| Număr de teste | ~18 funcții (1 parametrizat × 2 = 20 rulări) |
| Framework | pytest, funcții simple + markeri `@pytest.mark.xfail` |
| Structură | Listă plată de funcții, fără clase |

### Opus-4.7 (`Opus-4.7_tests.py`)
| Proprietate | Valoare |
|---|---|
| Număr de teste | ~40 metode de test în 10 clase + 1 clasă smoke-test |
| Framework | pytest, organizare bazată pe clase |
| Structură | 10 clase tematice: `TestActionSpace`, `TestReset`, `TestLegalMask`, `TestPawnMovement`, `TestPawnJumpRules`, `TestWallPlacement`, `TestTermination`, `TestApplyUndo`, `TestClone`, `TestEncoder`, `TestPolicyPermutation`, `TestRandomPlaySmoke` |

### Teste umane (directorul `tests/`)
| Fișier | Descriere |
|---|---|
| `test_functional_quoridor.py` | 13 metode de test în 2 clase — metodologie Black-Box EP + BVA |
| `test_structural_quoridor.py` | ~24 metode de test în 5 clase — testare White-Box / Structurală |
| `test_mutant_quoridor.py` | Runner extern pentru scor de mutanți (4 mutanți M1–M4, script non-pytest) |
| `test_mutation_killers.py` | 2 teste RSP-model mutation-killer (MTK-001, MTK-002) |
| **Total** | ~40+ funcții/metode de test în 4 fișiere |

---

## 2. Matricea de acoperire a funcționalităților

| Aspect | GPT-5.4 | Opus-4.7 | Uman |
|---|:---:|:---:|:---:|
| Consistența constantelor spațiului de acțiuni | NU | DA | NU |
| Stare inițială / `reset()` | DA | DA | Implicit |
| `reset(walls_left=...)` inițializare personalizată | NU | DA | NU |
| Forma și tipul măștii `legal_actions()` | DA | DA | Parțial |
| Numărul acțiunilor legale pe tablă goală | DA | DA | NU |
| `legal_actions()` returnează zero când `done` | NU | DA | NU |
| Mutări pion: normale | DA | DA | Parțial |
| Mutări pion: colț (doar 2 mutări) | NU | DA | NU |
| Mutări pion: nu poate călca pe adversar | DA | DA | NU |
| Salt pion: direct peste adversar | DA | DA | NU |
| Salt pion: diagonal (fallback cu zid) | DA | DA | NU |
| Salt pion: diagonal la marginea tablei | NU | DA | NU |
| Salt pion: nu poate reveni la sine | NU | DA | NU |
| Suprapunere zid `_overlaps_h` (3 direcții) | Parțial | DA | DA (ambele) |
| Suprapunere zid `_overlaps_v` (3 direcții) | NU | DA | DA (structural) |
| Intersecție ziduri `_crosses_h/v` | DA | DA | DA (structural) |
| Legalitate zid `_legal_h_wall` | DA | DA | DA (ambele, BVA detaliat) |
| Legalitate zid `_legal_v_wall` | NU | DA | DA (structural) |
| Buget de ziduri respectat | DA | DA | DA (ambele) |
| Zid în afara limitelor respins | NU | DA | DA (BVA funcțional) |
| Zid care blochează calea respins | DA | DA | DA (ambele) |
| Recompensă `step()`: 0 la mutare normală | DA | Implicit | NU |
| Recompensă `step()`: +1 la victorie (J0) | DA | DA | NU |
| Recompensă `step()`: +1 la victorie (J1) | NU | DA | NU |
| Recompensă `step()`: -1 la mutare ilegală | DA | DA | NU |
| Mutare ilegală → joc terminat | DA | DA | NU |
| `RuntimeError` la `step()` după terminare | DA | DA | NU |
| Corectitudinea schimbului de tur | DA | Implicit | DA (MTK) |
| Regula remiză la 3 repetiții | NU | DA | NU |
| `apply()` / `undo()` tur-retur pion | DA | DA | DA (structural) |
| `apply()` / `undo()` zid H (câmpuri owner) | DA | DA | DA (structural) |
| `apply()` / `undo()` zid V | DA | DA | DA (structural) |
| `apply()` / `undo()` restaurare mutare câștigătoare | NU | DA | NU |
| `apply()` / `undo()` lanț aleator (stres) | NU | DA (10×) | NU |
| Independența `clone()` | DA | DA | NU |
| `clone()` produce aceeași mască legală | NU | DA | NU |
| Forma și tipul `encode()` | DA | DA | NU |
| Planele pion/adversar în `encode_state()` | NU | DA | NU |
| Normalizarea `walls_left` în `encode_state()` | NU | DA | NU |
| Canonic = identitate pentru jucătorul 0 | DA | DA | NU |
| Canonic = rotație 180° pentru jucătorul 1 | DA | DA | NU |
| Canal goal-row canonic (ch. 6) | NU | DA | NU |
| Tur-retur `policy_to_canonical` J0 | DA | DA | NU |
| Tur-retur `policy_to_canonical` J1 | DA | DA | NU |
| Permutare politică: verificare matematică 180° | NU | DA | NU |
| `mask_to_canonical` conservă suma | DA | DA | NU |
| Test smoke aleatoriu (multe jocuri) | NU | DA (25 jocuri) | NU |
| Documentație limite EP/BVA | NU | NU | DA (extinsă) |
| Teste direcționate pe mutanți (model RSP) | NU | NU | DA (MTK-001/002) |
| Runner extern scor mutanți | NU | NU | DA (M1–M4) |
| Markeri `xfail` pentru bug-uri cunoscute | DA (3) | NU | NU |
| `_walls_sig_dirty` / cache | DA (xfail) | NU | DA (structural) |
| Acoperire directă `_blocked_with` | NU | NU | DA (9 cazuri) |
| Acoperire directă `_blocked_with_temp` | NU | NU | DA (3 cazuri) |
| Reutilizare / invalidare cache cale | NU | NU | DA (structural) |

---

## 3. Puncte forte și puncte slabe

### 3.1 GPT-5.4

#### Puncte forte
- **a)** Documentare onestă prin `xfail` a 3 bug-uri reale:
  - `clone()` nu copiază `walls_h_owner` / `walls_v_owner`
  - `step()` pe ramura cu zid nu setează `_walls_sig_dirty`
  - ID-urile de acțiuni în afara domeniului aruncă `IndexError` în loc să fie tratate ca ilegale

  Nicio altă suită nu semnalează aceste bug-uri.

- **b)** Testează `step()` ca metodă RL integrată — valori de recompensă, schimbul de tur, detectarea victoriei, garda `RuntimeError` — toate absente din suita umană.
- **c)** Salt pion drept + diagonal testat, inclusiv cazul de fallback diagonal declanșat de un zid în spatele adversarului.
- **d)** Simetria canonică și tur-retrul politicii testate, acoperind o proprietate de corectitudine specifică AlphaZero, absentă din suita umană.
- **e)** Independența copiei profunde `clone()` verificată.

#### Puncte slabe
- **a)** Cea mai mică suită (~20 rulări). Multe căi importante nu sunt atinse.
- **b)** Niciun test pentru ziduri verticale (`_legal_v_wall` nu este apelat niciodată direct).
- **c)** Doar recompensa de victorie a J0 este testată; victoria J1 este omisă.
- **d)** Niciun test de mutare din colț; niciun test „nu poate călca pe adversar".
- **e)** Niciun test de salt pion la marginea tablei.
- **f)** Regula remiză la 3 repetiții complet absentă.
- **g)** `reset(walls_left=...)` nu este testat.
- **h)** Revenirea mutării câștigătoare prin `apply/undo` nu este testată.
- **i)** Niciun test smoke/fuzz.
- **j)** Nicio metodologie documentată; intenția trebuie dedusă din cod.

---

### 3.2 Opus-4.7

#### Puncte forte
- **a)** Cea mai largă acoperire dintre cele trei suite. Singura suită care testează **toate** acestea:
  - Regula remiză la 3 repetiții (`test_threefold_repetition_draws`)
  - `reset(walls_left=...)` inițializare personalizată
  - `legal_actions()` returnează zero când `env.done` este `True`
  - Pion în colț cu exact 2 mutări
  - Regula „nu poate călca pe adversar"
  - Salt pion la marginea tablei (diagonal forțat deoarece rândul -1 este în afara tablei)
  - Siguranța „saltul nu poate reveni la sine"
  - Detectarea victoriei J1 (recompensă +1)
  - `apply/undo` pe o mutare câștigătoare (restaurează `done`, `winner`, `player`)
  - Lanț aleator de 10 pași `apply/undo` (test de stres)
  - `clone()` produce aceeași mască legală ca originalul
  - Valorile planelor pion și adversar din `encode_state()`
  - Normalizarea `walls_left` în planele 4 și 5 ale encoder-ului
  - Conținutul canalului goal-row canonic (canalul 6)
  - Verificare matematică rotație 180° pentru `policy_to_canonical`
  - Test smoke aleatoriu (25 de jocuri cu bias spre mutare înainte)
  - Consistența constantelor spațiului de acțiuni (`TestActionSpace`)

- **b)** Testele de plasare a zidurilor acoperă ambele orientări cu mai multe cazuri de adiacență (același slot, adiacent stânga/dreapta pentru ziduri H; același slot, adiacent sus/jos pentru ziduri V) plus un scenariu matematic de capcană în colț.
- **c)** Testele `apply/undo` sunt cele mai complete: pion, zid H, zid V, mutare câștigătoare și un lanț aleator de 10 mutări — fiecare cu comparație completă de stare inclusiv array-urile owner și `walls_left`.
- **d)** Structură clară bazată pe clase, lizibilă, cu comentarii doc care explică intenția.
- **e)** Helpere auto-conținute (`_snapshot`, `_equal`, `_legal_pawn_targets`) îmbunătățesc lizibilitatea și reutilizarea.

#### Puncte slabe
- **a)** Zero testare de mutanți. Niciun marker `xfail`, niciun test RSP-model, niciun runner extern de scor mutanți.
- **b)** Nicio documentație EP/BVA. Valorile de frontieră sunt exercitate pe alocuri, dar niciodată denumite sau justificate sistematic.
- **c)** `_blocked_with` și `_blocked_with_temp` nu sunt niciodată apelate direct. Suita structurală umană le acoperă cu 12 cazuri parametrizate.
- **d)** Corectitudinea cache-ului de cale (reutilizare pe aceeași cheie, cheie nouă după schimbarea zidului) nu este verificată.
- **e)** Nicio documentație de bug-uri cunoscute. Cele trei bug-uri găsite de markerii `xfail` ai GPT-5.4 nu sunt semnalate deloc.
- **f)** Afirmația din smoke test `sum(terminations.values()) == n_games` este trivial adevărată deoarece „stalled" incrementează contorul; nu dovedește că fiecare joc se termină printr-o regulă reală de joc.

---

### 3.3 Teste umane

#### Puncte forte
- **a)** Singura suită cu metodologie riguroasă și trasabilă. Fiecare clasă de teste denumește partiția de echivalență sau valoarea de frontieră vizată, făcând suita auditabilă și ușor de întreținut.
- **b)** Singura suită cu testare de mutanți:
  - `test_mutant_quoridor.py`: runner automat pentru 4 mutanți, raportează scorul.
  - `test_mutation_killers.py`: RSP-model killers pentru 2 mutanți supraviețuitori (MTK-001, MTK-002), fiecare cu o schiță de demonstrație.
- **c)** `_blocked_with` și `_blocked_with_temp` sunt testate direct cu 12 cazuri parametrizate — cea mai temeinică acoperire a subsistemului de blocare a mișcării.
- **d)** `apply/undo` verifică array-urile owner (`walls_h_owner`, `walls_v_owner`) și `walls_left` pe lângă prezența zidurilor.
- **e)** Reutilizarea și invalidarea cache-ului de cale verificate ca gardă de regresie.
- **f)** `_overlaps_h`, `_overlaps_v` acoperite pentru toate cele trei direcții de adiacență.
- **g)** BVA pentru `_legal_h_wall`: 4 combinații valide de frontieră (colțurile grilei de ziduri) plus 5 condiții de frontieră invalide sunt explicit denumite și testate.

#### Puncte slabe
- **a)** `step()` nu este apelat niciodată. Interfața RL primară — recompense, schimbul de tur, detectarea câștig/pierdere, regula de remiză, garda `RuntimeError` — este complet netestată.
- **b)** Niciun test de salt al pionului de niciun fel.
- **c)** `encode()`, `encode_state_canonical()` și funcțiile canonice policy/mask nu sunt niciodată exercitate.
- **d)** `clone()` niciodată testat.
- **e)** Regula remiză la 3 repetiții netestată.
- **f)** `reset(walls_left=...)` netestat.
- **g)** Scopul este limitat efectiv la subsistemul de plasare a zidurilor.

---

## 4. Contribuții unice pe suită

**Doar GPT-5.4 găsește / documentează:**
- Bug cunoscut: `clone()` nu copiază array-ul owner *(xfail)*
- Bug cunoscut: `step()` nu invalidează `_walls_sig` *(xfail)*
- Bug cunoscut: acțiunile în afara domeniului aruncă `IndexError` *(xfail)*

**Doar Opus-4.7 testează:**
- Regula remiză la 3 repetiții
- `reset(walls_left=...)` inițializare personalizată
- `legal_actions()` == 0 când terminat
- Mutarea pionului din colț (exact 2 mutări)
- „Nu poate călca pe adversar" în mod explicit
- Salt pion la marginea tablei
- „Saltul nu poate reveni la sine"
- Recompensa de victorie J1 (+1.0)
- `apply/undo` pe o mutare câștigătoare (restaurare `done`/`winner`/`player`)
- Lanț aleator `apply/undo` (stres 10 pași)
- `clone()` produce aceeași mască legală
- Conținutul canalelor `encode_state()` (pion, normalizare `walls_left`, goal row)
- Verificare matematică rotație 180° pentru `policy_to_canonical`
- Test smoke aleatoriu (25 jocuri)
- Consistența constantelor spațiului de acțiuni

**Doar testele umane acoperă:**
- Metodologia de frontieră EP/BVA cu documentație completă
- RSP-model mutation killers (MTK-001, MTK-002)
- Runner extern scor mutanți (M1–M4)
- Teste parametrizate directe pentru `_blocked_with` / `_blocked_with_temp`
- Regresia reutilizării și invalidării cache-ului de cale

---

## 5. Rezumat cantitativ

| Metric | GPT-5.4 | Opus-4.7 | Uman |
|---|:---:|:---:|:---:|
| Nr. aproximativ de teste | ~20 | ~45 | ~40+ |
| Apeluri distincte de clase/metode exercitate | 11 | 18 | 10 |
| Integrare `step()` testată | DA | DA | NU |
| Conținut `encode()` verificat | Parțial | DA | NU |
| Simetrie canonică testată | DA | DA | NU |
| `clone()` testat | DA | DA | NU |
| Mecanica saltului testată | DA | DA | NU |
| Regula de remiză 3 repetări testată | NU | DA | NU |
| `reset(walls_left)` testat | NU | DA | NU |
| Adâncimea `apply/undo` | 3 acțiuni | 10 acțiuni | 2 acțiuni |
| Adâncimea predicatelor de zid | MEDIE | ÎNALTĂ | ÎNALTĂ (BVA/EP) |
| Teste directe `_blocked_with` | NU | NU | DA (12 cazuri) |
| Testare de mutanți | NU | NU | DA (RSP + runner) |
| Documentație bug-uri cunoscute | DA (3) | NU | NU |
| Testare smoke / fuzz | NU | DA | NU |
| Documentație cod / metodologie | SCĂZUTĂ | MEDIE | ÎNALTĂ |

---

## 6. Verdict și clasament

### Clasament: Opus-4.7 > Uman > GPT-5.4

#### Opus-4.7 — 8.5 / 10
Cea mai puternică suită în ansamblu. Este singura care testează regula de remiză la 3 repetări, reset personalizat, `apply/undo` pe mutări câștigătoare, salt pion la margine și un test smoke aleatoriu. Amploarea sa structurală și lizibilitatea o fac cel mai bun fișier de teste independent. Principalul deficit este absența completă a testării de mutanți și a documentației bug-urilor cunoscute.

#### Uman — 7.5 / 10
Cea mai riguroasă suită din punct de vedere metodologic și singura care oferă testare de mutanți (atât un runner de scor cât și RSP-model killers). Cu toate acestea, este limitată aproape exclusiv la subsistemul de ziduri și nu exercită niciodată interfața RL (`step()`) sau stratul de simetrie/encodare — un punct orb critic pentru un mediu RL.

#### GPT-5.4 — 6.5 / 10
Acoperă preocupările corecte de nivel înalt (`step()`, simetrie, salturi) și documentează unic trei bug-uri reale prin markeri `xfail`. Cu toate acestea, este cea mai mică suită, ratează victoria J1, regula de remiză și nu are teste pentru ziduri verticale. Utilă ca supliment, dar insuficientă singură.


