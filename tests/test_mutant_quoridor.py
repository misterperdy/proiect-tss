import os
import subprocess
import shutil

TARGET_FILE = "../Quoridor_Class.py"
BACKUP_FILE = "../Quoridor_Class.original.py"

MUTANTS = [
    {
        "id": "M1",
        "op": "Relational Operator Replacement",
        "original": "0 <= wr < wall_grid_size",
        "mutated": "0 < wr < wall_grid_size",
        "description": "Schimba limita inferioara a randului de la >= la >"
    },
    {
        "id": "M2",
        "op": "Relational Operator Replacement",
        "original": "self.walls_left[self.player] <= 0",
        "mutated": "self.walls_left[self.player] == 0",
        "description": "Schimba verificarea inventarului (ignora valorile negative)"
    },
    {
        "id": "M3",
        "op": "Constant Replacement",
        "original": "self.walls_h[wr, wc] = 1",
        "mutated": "self.walls_h[wr, wc] = 2",
        "description": "Schimba valoarea de marcare a zidului in matrice"
    },
    {
        "id": "M4",
        "op": "Arithmetic Operator Replacement",
        "original": "self.player ^= 1",
        "mutated": "self.player = 1",
        "description": "Distruge mecanismul de schimbare a jucatorului"
    }
]


def run_pytest():

    result = subprocess.run(["python", "-m", "pytest", "--tb=no", "-q"], capture_output=True, text=True)
    return result.returncode == 0


def main():
    print("Analysis: ...")

    if not os.path.exists(TARGET_FILE):
        print(f"Eroare: {TARGET_FILE} NOT FOUND")
        return


    shutil.copyfile(TARGET_FILE, BACKUP_FILE)

    with open(TARGET_FILE, "r", encoding="utf-8") as f:
        p_code = f.read()

    results = []
    distinguished_count = 0

    for m in MUTANTS:
        if m["original"] not in p_code:
            continue

        m_code = p_code.replace(m["original"], m["mutated"], 1)

        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            f.write(m_code)

        all_tests_passed = run_pytest()

        status = "ALIVE" if all_tests_passed else "KILLED"
        if not all_tests_passed:
            distinguished_count += 1

        results.append((m["id"], m["op"], status, m["description"]))
        print(f"   > {m['id']}: {status} ({m['op']})")

        with open(TARGET_FILE, "w", encoding="utf-8") as f:
            f.write(p_code)

    if os.path.exists(BACKUP_FILE):
        os.remove(BACKUP_FILE)

    print("\n")
    print(f"{'ID':<5} | {'Operator':<30} | {'Status'}")

    for res in results:
        print(f"{res[0]:<5} | {res[1]:<30} | {res[2]}")

    total = len(results)
    live_non_equivalent = total - distinguished_count

    if total > 0:
        ms = distinguished_count / total
        print(f"Mutanti distrusi: {distinguished_count} ")
        print(f"Mutanti in viata : {live_non_equivalent} ")
        print(f"Scor/Procent = {ms:.2f} (sau {ms * 100:.1f}%) ")



if __name__ == "__main__":
    main()