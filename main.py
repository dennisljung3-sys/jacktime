# main.py
import os
from meny import huvudmeny
from tools.error_logger import logga_fel, logga_meddelande
from fönsterhanterare import FönsterHanterare, set_fönster

# Lista över alla viktiga mappar
nödvändiga_mappar = ["resultat", "startlistor", "träning", "data", "logs"]

# Skapa dem om de inte finns
for mapp in nödvändiga_mappar:
    os.makedirs(mapp, exist_ok=True)


def main():
    logga_meddelande("info", "Programmet startar...")

    # Skapa och visa fönsterhanteraren
    fönster = FönsterHanterare()
    fönster.skapa_fönster()

    # Spara instansen så att andra moduler kan komma åt den
    set_fönster(fönster)

    # Visa startsida (håller fönstret öppet och responsivt)
    fönster.visa_startsida()

    try:
        huvudmeny()
    except Exception as e:
        logga_fel(e)
        print("❌ Programmet krashade. Se logs/error_log.txt för detaljer.")
    finally:
        # Stäng fönsterhanteraren när programmet avslutas
        if fönster:
            fönster.stäng()


if __name__ == "__main__":
    main()
