import logging
import os
import traceback

# 📂 Loggfilen hamnar i samma mapp som denna modul
LOGFIL = os.path.join(os.path.dirname(__file__), "error_log.txt")

# 🔧 Konfigurera loggern
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGFIL, encoding="utf-8"),
        logging.StreamHandler()  # skriver även till konsolen
    ]
)


def logga_fel(e: Exception):
    """
    Loggar ett undantag till error_log.txt och konsolen.
    """
    feltext = f"{str(e)}\n{traceback.format_exc()}"
    logging.error(feltext)


def logga_meddelande(nivå: str, meddelande: str):
    """
    Loggar ett vanligt meddelande (info, warning, error).
    """
    nivå = nivå.lower()
    if nivå == "info":
        logging.info(meddelande)
    elif nivå == "warning":
        logging.warning(meddelande)
    elif nivå == "error":
        logging.error(meddelande)
    else:
        logging.debug(meddelande)
