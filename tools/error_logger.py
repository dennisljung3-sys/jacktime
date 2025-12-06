import logging
import os
import traceback
from collections import deque
import sys

# 📂 Loggfilen hamnar i samma mapp som denna modul
LOGFIL = os.path.join(os.path.dirname(__file__), "error_log.txt")

# 🔧 Konfigurera loggern
logging.basicConfig(
    level=logging.ERROR,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler(LOGFIL, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

# Ringbuffer för senaste raderna (nu 20 istället för 15)
terminal_buffer = deque(maxlen=20)


class BufferStream:
    """Wrapper runt sys.stdout/sys.stderr som sparar rader i en buffer."""

    def __init__(self, stream):
        self.stream = stream

    def write(self, text):
        if text.strip():  # hoppa över tomma rader
            terminal_buffer.append(text.strip())
        self.stream.write(text)

    def flush(self):
        self.stream.flush()


# Byt ut stdout och stderr mot vår wrapper
sys.stdout = BufferStream(sys.stdout)
sys.stderr = BufferStream(sys.stderr)


def logga_fel(e: Exception):
    """
    Loggar ett undantag + senaste 20 raderna från terminalen.
    """
    feltext = f"{str(e)}\n{traceback.format_exc()}"
    logging.error(feltext)

    # Lägg till buffrade rader
    logging.error("Senaste terminalrader innan kraschen:")
    for rad in terminal_buffer:
        logging.error(rad)


def logga_meddelande(nivå: str, meddelande: str):
    nivå = nivå.lower()
    if nivå == "info":
        logging.info(meddelande)
    elif nivå == "warning":
        logging.warning(meddelande)
    elif nivå == "error":
        logging.error(meddelande)
    else:
        logging.debug(meddelande)
