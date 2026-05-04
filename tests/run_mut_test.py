import os
import subprocess
import sys

CONFIG_FILE = "quoridor.toml"
DB_FILE = "quoridor.sqlite"
HTML_REPORT = "report.html"


def run_command(command, description):
    print(f" {description}")
    print(f"{command}")

    # Rulăm comanda în terminal
    result = subprocess.run(command, shell=True)

    if result.returncode != 0:
        print(f"\n Eroare!")
        sys.exit(1)


def main():

    if os.path.exists(DB_FILE):
        os.remove(DB_FILE)
        print(f"Old db '{DB_FILE}' was removed .")#Deleting db

    run_command(f"cosmic-ray init {CONFIG_FILE} {DB_FILE}", "Generating mutants") #Generam mutantii

    print("This is gonna take a while")
    run_command(f"cosmic-ray exec {CONFIG_FILE} {DB_FILE}", "Executing mutants")#Verificam

    run_command(f"cr-rate {DB_FILE}", "Calculating mutant score")#Calculam scorul

    run_command(f"cr-html {DB_FILE} > {HTML_REPORT}", "Raport HTML")#Creem raportul

    print(f"Finished")#Over


if __name__ == "__main__":
    main()