# Documentație: Testarea Structurală (White-Box)

## 1. Introducere și Obiective

Această secțiune detaliază abordarea aleasă pentru etapa de Testare Structurală a mediului de joc Quoridor (clasa `QuoridorEnv`). Obiectivul principal a fost validarea logicii interne a metodelor critice, asigurând acoperirea instrucțiunilor, a deciziilor (Branch Coverage) și identificarea circuitelor independente, conform standardelor de testare software.

Având în vedere complexitatea ridicată a validărilor din joc (ex. algoritmul de *pathfinding* și verificarea suprapunerilor de pereți), am optat pentru dezvoltarea unui **cadru de testare automatizat propriu**, care îmbină analiza statică a codului cu Inteligența Artificială Generativă.

---

## 2. Analiza Fluxului de Control și Circuitele Independente

Pentru a satisface cerința identificării circuitelor independente, este necesară trasarea Grafurilor Fluxului de Control (CFG) și calcularea Complexității Ciclomatice. În loc să realizăm acest proces manual, am dezvoltat un modul de analiză automată (`graph_generator.py`).

**Metodologia utilizată:**
* Am folosit biblioteca nativă `ast` (Abstract Syntax Tree) din Python pentru a parsa codul sursă al clasei `QuoridorEnv`.
* Scriptul identifică toate nodurile de decizie (`if`, `elif`, bucle) și generează automat reprezentarea vizuală a grafului sub formă de cod *Mermaid*.
* Totodată, algoritmul calculează automat elementele de control și **Complexitatea Ciclomatică** pentru fiecare metodă analizată.

**Rezultate obținute:** Au fost analizate 20 de metode principale ale proiectului. Toate grafurile rezultate, împreună cu detaliile aferente, au fost exportate cu succes în directorul `tests/control_flow_graphs/`.

---

## 3. Acoperirea Deciziilor (Branch Coverage) prin Agenți AI

Pentru scrierea testelor unitare care să parcurgă fiecare ramură decizională extrasă anterior, am creat un script de generare (`generate_tests.py`), orchestrat de un agent inteligent (`test_generator/ai_agent.py`) conectat la API-ul Google Gemini.

**Fluxul de execuție al agentului (The Agentic Loop):**
1. **Contextualizare:** Sistemul trimite către modelul de limbaj (LLM) codul sursă al unei metode și o condiție specifică extrasă din CFG (de exemplu: determină testul să intre pe ramura `if r2 == r1 + 1:`).
2. **Generare:** LLM-ul redactează o funcție de test folosind framework-ul `pytest`, incluzând datele de intrare (mock-uri) necesare pentru a forța evaluarea condiției respective ca fiind adevărată.
3. **Validare și Auto-Corectare:** Inovația acestui flux constă în validarea locală. Agentul rulează imediat testul generat în fundal. Dacă testul eșuează (ex. dintr-o eroare de logică sau un atribut inexistent), agentul preia direct raportul de eroare (Traceback) din terminal și îl trimite înapoi modelului Gemini cu instrucțiunea de a corecta codul. Procesul se repetă de până la 5 ori (cu *exponential backoff* în caz de limitare API) până la obținerea unui test valid (PASSED).

---

## 4. Configurația Mediului de Lucru

Pentru această etapă, configurația a fost următoarea:
* **Hardware:** Execuție locală pe mașina fizică a echipei (fără utilizarea unei mașini virtuale - VM).
* **Sistem de Operare:** Windows 10.
* **Mediu Software:** Python 3.10+, framework-ul `pytest` pentru rularea testelor.
* **Integrări externe:** SDK-ul `google-genai` conectat la Google AI Studio (utilizând modelul `gemini-2.5-flash` pentru generarea rapidă și deterministă a testelor).

---

## 5. Execuție și Validare

Testele generate automat au fost salvate în fișierul `tests/test_structural_quoridor.py`. Pentru a verifica acoperirea ramurilor și succesul testelor, se folosește următoarea comandă în terminal:

```bash
python -m pytest tests/test_structural_quoridor.py -v
```

Acest ansamblu de teste se concentrează excepțional pe validările de plasare a pereților temporari și permanenți (ex: metodele `_blocked_with_temp`), demonstrând că ramurile care preiau excepții sau limite aspre ale hărții funcționează conform specificațiilor interne ale claselor.

---

## 6. Concluzii

Prin această abordare hibridă, am reușit să automatizăm nu doar extragerea metodelor de calcul pentru Complexitatea Ciclomatică, ci și generarea masivă a suitei *White-Box*. Framework-ul de testare obținut garantează o testare scalabilă și o acoperire metodologică net superioară raportat la scrierea tradițională (manuală) a testelor structurale.
