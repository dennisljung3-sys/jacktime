import os
from meny import huvudmeny
from tools.error_logger import logga_fel, logga_meddelande

# Lista över alla viktiga mappar
nödvändiga_mappar = [
    "resultat",
    "startlistor",
    "träning",
    "data"
]

# Skapa dem om de inte finns
for mapp in nödvändiga_mappar:
    os.makedirs(mapp, exist_ok=True)


def main():
    logga_meddelande("info", "Programmet startar...")
    try:
        huvudmeny()
    except Exception as e:
        logga_fel(e)
        print("X Programmet krashade. Se tools/error_log.txt för detaljer.")


if __name__ == "__main__":
    main()
