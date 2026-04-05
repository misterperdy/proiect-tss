# Documentatie: Testarea Functionala a clasei QuoridorEnv

Acest fisier documenteaza procesul de testare functionala (de tip black-box) aplicat pe structura de baza a jocului Quoridor, mai precis pe clasa `QuoridorEnv`. Obiectivul a fost verificarea corectitudinii jocului pe baza intrarilor si iesirilor, facand abstractie de implementarile din spate ale codului.

Pentru realizarea acestui set de teste, s-au utilizat doua tehnici standard de testare software predate la curs:
* **Partitionarea in Clase de Echivalenta (EP)**
* **Analiza Valorilor de Frontiera (BVA)**

Mediul folosit pentru rularea si organizarea testelor este framework-ul `pytest`.

---

## Logica jocului si limitele clasei

Clasa `QuoridorEnv` contine logica pentru plasarea pionilor pe o tabla de 9x9 si plasarea peretilor pe o tabla interna de 8x8 (indexata de la 0 la 7).

Orice actiune, cum ar fi incercarea de a aseza un perete, trece printr-o serie de validari complexe. Sistemul verifica daca peretele iese in afara tablei, daca se suprapune cu un alt perete existent, daca intersecteaza o piesa similara in forma de cruce sau, foarte important, daca mutarea respectiva blocheaza complet drumul pionului advers catre linia de final.

Pentru a demonstra tehnicile de testare functionala pe acest model, am selectat validarea si restrictiile plasarii peretilor orizontali.

---

## Modul de organizare a testelor

### Validarea suprapunerilor (Overlaps H)

Functia `_overlaps_h(self, wr, wc)` verifica strict daca pozitia pe care se doreste plasarea unui perete orizontal este deja ocupata sau obstructionata de ceva existent pe aceeasi axa.

Au fost identificate 4 clase de echivalenta distincte, ce acopera integral starea tablei de joc:

| Clasa | Conditie de testare | Output asteptat | Explicatie aplicativa |
| :--- | :--- | :--- | :--- |
| **S_1** | Exista deja perete pe aceeasi locatie | `True` | Se incearca plasarea de perete fix la locatia (3,3) peste altul pus la (3,3). |
| **S_2** | Perete care obstructioneaza din stanga | `True` | Un perete existent la (3,2) extins blocheaza spatiul cerut initial. |
| **S_3** | Perete care obstructioneaza din dreapta | `True` | Un perete existent la (3,4) extins blocheaza locatia curenta. |
| **S_4** | Tabla este complet libera | `False` | Lipsa vreunui obstacol invecinat pe directia respectiva, permitand plasarea. |

---

### Verificarea finala a mutarilor (BVA si EP)

Functia `_legal_h_wall(self, wr, wc)` raspunde de decizia finala privind legalitatea oricarei actiuni de plasare orizontala. Avand in vedere ca aduce cu sine validari pentru toate mecanicile jocului in acelasi timp, s-a impus organizarea testelor direct pe limitele matricei prin Analiza Valorilor de Frontiera (BVA), pe langa conditiile de mediu.

Parametrii principali testati au fost randurile (`wr`), coloanele (`wc`) si stocul de pereti in sine (`walls_left`). Frontierele logice detectate conform documentatiei sunt:
* Cazul randurilor si coloanelor din tabla permit setari in intervalul de incadrare natural intre 0 si 7. Marginea pe frontiere sigure se testeaza la extremitatile de colt la valoarile **0 si 7**.
* In consecinta, depasirile minime si primele elemente pur invalide se afla la o mutare distanta, respectiv valorile limitrofe eronate **-1** si **8**.
* Stocul unui jucator curge in joc de la limita inferioara pana la 10 (cifra peretilor disponibili limitati per jucator). In conditii de limitare impusa se ajunge la limita interzisa de validare pe bariera insemnand **0 pereti ramasi**.

Sub aceste premize, constructia noastra acopera complet limitele pe frontiera plus bariere de regulament:

| Metoda de test in script | Frontiera validata / Clasa EP | Parametrii de setat tehnic | Output astetapt |
| :--- | :--- | :--- | :--- |
| `test_bva_1_top_left_edge` | BVA valid: Coltul stanga-sus si epuizare de limita a resurselor. | `wr=0`, `wc=0`, `walls=1` | `True` |
| `test_bva_2_top_right_edge`| BVA valid: Coltul dreapta-sus complet. | `wr=0`, `wc=7`, `walls=10`| `True` |
| `test_bva_3_bottom_left_edge` | BVA valid: Coltul stanga-jos valid sub frontiera inferioara. | `wr=7`, `wc=0`, `walls=1` | `True` |
| `test_bva_4_bottom_right_edge`| BVA valid: Coltul dreapta-jos. | `wr=7`, `wc=7`, `walls=10`| `True` |
| `test_bva_c2_invalid_row_negative` | BVA invalid: Coordonata pe minus. Intrare gresita catre array. | `wr=-1`, `wc=3` | `False` |
| `test_bva_c3_invalid_row_too_large`| BVA invalid: Depasirea cadrului superioard cu o unitate.| `wr=8`, `wc=3` | `False` |
| `test_bva_c4_invalid_col_negative` | BVA invalid: Impingerea coordonatei in minus negativ.| `wr=3`, `wc=-1` | `False` |
| `test_bva_c5_invalid_col_too_large`| BVA invalid: Cresterea dimensiunii cerute catre dreapta si interzis.| `wr=3`, `wc=8` | `False` |
| `test_bva_c6_no_walls_left` | BVA invalid: Test cand stocul curent s-a ridicat epuizat si arata frontiera bariera zero. | `walls=0` pe rand | `False` |
| `test_ep_c7_horizontal_overlap` | EP state: Un caz normal unde peretele cerut intampinat cu perete inserat din stanga. | Situatie de suprapunere dubla directa pe (3,3) | `False` |
| `test_ep_c8_vertical_crossing` | EP state: Caz din pathfinding direct cand e interzis intre doi pereti pe alta axa intersectati total cruci. | Caz intersescare orizontal versus vertical luat decizie pe centru. | `False` |
| `test_ep_c9_blocks_path_to_goal`| EP state: Analiza de pathfinding logic in care bariera va cauza izolarea unui actor. Regulament interzis. | Constructia unei capcane perfect cu pereti verticali lasand doar intrarea sus pentru baricadare ulterioara perfect in scopul peretelui de incercare. | `False` |

---

## Concluzii suita limitrofa finala

Folosirea unei metodologii testate ca Partitionarea in Clase de Echivalenta combinata foarte curat cu o Analiza pe Valorile de Frontiera are aplicabilitate instantanee si eficacitate maxima. Dintr-o multitudine astronomica de situatii aleatoare pe grid-ul de joc, validarea functionalitatii logice intregi se reduce prin simplificare conceptuala la numai **16 cazuri teste riguros selectate**.

Acest nivel restrange munca programatorului dar ofera incredere, nefind nevoie insa sa caute random ci doar acoperind zonele extreme sau regulile izolate din motor.

Comanda normala de executie standard daca o rulam local pentru tot pachetul ar fi:

```bash
python -m pytest tests/test_functional_quoridor.py -v
```
