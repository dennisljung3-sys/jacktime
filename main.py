# main.py
import os
import atexit
from meny import huvudmeny
from tools.error_logger import logga_fel, logga_meddelande
from fönsterhanterare import FönsterHanterare, set_fönster
from fifo_input import (
    starta_fifo_lyssnare,
    stoppa_fifo_lyssnare,
    rensa_status,
    skriv_status,
)

# Lista över alla viktiga mappar
nödvändiga_mappar = ["resultat", "startlistor", "träning", "data", "logs"]

# Skapa dem om de inte finns
for mapp in nödvändiga_mappar:
    os.makedirs(mapp, exist_ok=True)


def _städa_vid_avslut():
    """Städar FIFO och statusfil när programmet avslutas."""
    try:
        skriv_status("avslutad")
    except Exception:
        pass
    stoppa_fifo_lyssnare()
    rensa_status()


def main():
    logga_meddelande("info", "Programmet startar...")

    # ⭐ Starta FIFO-lyssnaren först av allt
    starta_fifo_lyssnare()

    # Registrera städning vid avslut (Ctrl+C, normal exit, etc.)
    atexit.register(_städa_vid_avslut)

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
