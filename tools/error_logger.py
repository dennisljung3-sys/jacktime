# tools/error_logger.py
import logging
import os
import sys
import traceback
from datetime import datetime


def get_log_path():
    """
    Returnerar rätt sökväg för loggfilen, oavsett om programmet körs
    som Python-skript eller som paketerad exekverbar fil.
    """
    if getattr(sys, "frozen", False):
        # Paketerad exekverbar fil - spara i samma mapp som exekverbarfilen
        base_path = os.path.dirname(sys.executable)
    else:
        # Python-skript - spara i projektets rotmapp (en nivå upp från tools)
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Skapa logs-mapp om den inte finns
    log_dir = os.path.join(base_path, "logs")
    os.makedirs(log_dir, exist_ok=True)

    return os.path.join(log_dir, "error_log.txt")


# 🔧 Konfigurera loggern med dynamisk sökväg
LOGFIL = get_log_path()

# Skapa loggern
logger = logging.getLogger("jacktime")
logger.setLevel(logging.ERROR)

# Skapa formatterare
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

# Fil-handler (sparar till fil)
try:
    file_handler = logging.FileHandler(LOGFIL, encoding="utf-8", mode="a")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
except Exception as e:
    # Om vi inte kan skapa fil-handler, fortsätt ändå
    print(f"Varning: Kunde inte skapa loggfil: {e}")

# Konsol-handler (skriver till terminal)
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


def logga_fel(e: Exception):
    """
    Loggar ett undantag till error_log.txt och konsolen.
    """
    feltext = f"{str(e)}\n{traceback.format_exc()}"
    logger.error(feltext)


def logga_meddelande(nivå: str, meddelande: str):
    """
    Loggar ett vanligt meddelande (info, warning, error).
    """
    nivå = nivå.lower()
    if nivå == "info":
        logger.info(meddelande)
    elif nivå == "warning":
        logger.warning(meddelande)
    elif nivå == "error":
        logger.error(meddelande)
    else:
        logger.debug(meddelande)


# Testfunktion (kan tas bort i produktion)
def test_loggning():
    """Testa att loggningen fungerar"""
    logga_meddelande("info", "Testmeddelande - info")
    logga_meddelande("warning", "Testmeddelande - warning")

    try:
        x = 1 / 0
    except Exception as e:
        logga_fel(e)

    print(f"✅ Loggningen fungerar! Loggfil: {LOGFIL}")
