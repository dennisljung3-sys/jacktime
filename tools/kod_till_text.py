import os

def samla_kod_med_rader(källmapp, utfil):
    summering = []

    with open(utfil, "w", encoding="utf-8") as ut:
        for filnamn in sorted(os.listdir(källmapp)):
            if filnamn.endswith(".py"):
                full_path = os.path.join(källmapp, filnamn)
                ut.write(f"\n\n# --- {filnamn} ---\n\n")
                radantal = 0
                with open(full_path, "r", encoding="utf-8") as f:
                    for i, rad in enumerate(f, start=1):
                        ut.write(f"{i:>4}: {rad}")
                        radantal += 1
                summering.append((filnamn, radantal))

        # Lägg till summering i slutet
        ut.write("\n\n# --- Summering ---\n\n")
        for namn, antal in summering:
            ut.write(f"{namn:<30} {antal:>5} rader\n")

# Exempelanvändning:
källmapp = "/home/dennis/test_git/jacktime"
utfil = "/home/dennis/test_git/jacktime/tools/Tidtagning_Project.txt"

samla_kod_med_rader(källmapp, utfil)
