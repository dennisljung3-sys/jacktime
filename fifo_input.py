# fifo_input.py
"""
FIFO-baserad kommunikation mellan GUI och terminal.

GUI:t skickar kommandon till /tmp/jacktime_input (FIFO).
Terminalen läser från kön och agerar som om användaren skrivit i terminalen.
Terminalen skriver status till /tmp/jacktime_status.json som GUI:t läser.

Fallback: Om FIFO:n inte finns används vanligt input() precis som idag.
Tangentbordet fungerar alltid parallellt med FIFO:n.
"""

import os
import json
import queue
import threading
import time
import sys


# === Sökvägar ===
FIFO_PATH = "/tmp/jacktime_input"
STATUS_PATH = "/tmp/jacktime_status.json"


# === Global kö för inkommande kommandon ===
_tangent_kö = queue.Queue()

# === Global flagga för om FIFO-lyssnaren är igång ===
_fifo_aktiv = False

# === Global flagga för om tangentbords-lyssnaren är igång ===
_tangentbord_aktiv = False


# ============================================================
# FIFO-lyssnaren
# ============================================================

def starta_fifo_lyssnare():
    """
    Skapar FIFO-filen och startar en bakgrundstråd som läser från den.
    Varje rad som läses läggs i _tangent_kö.
    """
    global _fifo_aktiv

    # Ta bort gammal FIFO om den finns
    if os.path.exists(FIFO_PATH):
        try:
            os.remove(FIFO_PATH)
        except OSError:
            pass

    # Skapa FIFO
    try:
        os.mkfifo(FIFO_PATH)
    except OSError as e:
        print(f"⚠️ Kunde inte skapa FIFO: {e}")
        return

    _fifo_aktiv = True

    def lyssna():
        """Bakgrundstråd som läser från FIFO och lägger kommandon i kön."""
        while _fifo_aktiv:
            try:
                # Öppna FIFO för läsning. Blockerar tills någon skriver.
                with open(FIFO_PATH, "r") as fifo:
                    for rad in fifo:
                        kommando = rad.strip()
                        if kommando:
                            _tangent_kö.put(kommando)
                        else:
                            # Tom rad = Enter
                            _tangent_kö.put("")
            except OSError:
                # FIFO kan ha tagits bort – försök igen
                time.sleep(0.1)

    tråd = threading.Thread(target=lyssna, daemon=True)
    tråd.start()
    print(f"✅ FIFO-lyssnare startad: {FIFO_PATH}")


def stoppa_fifo_lyssnare():
    """Stoppar FIFO-lyssnaren och tar bort FIFO-filen."""
    global _fifo_aktiv
    _fifo_aktiv = False
    if os.path.exists(FIFO_PATH):
        try:
            os.remove(FIFO_PATH)
        except OSError:
            pass


# ============================================================
# Tangentbords-lyssnaren (körs parallellt med FIFO:n)
# ============================================================

def _starta_tangentbords_lyssnare():
    """
    Startar en bakgrundstråd som läser från stdin och lägger rader i samma kö.
    Detta gör att tangentbordet fungerar parallellt med FIFO:n.
    """
    global _tangentbord_aktiv
    _tangentbord_aktiv = True

    def lyssna():
        """Läser rader från stdin och lägger dem i kön."""
        while _tangentbord_aktiv:
            try:
                rad = sys.stdin.readline()
                if rad == "":
                    # EOF – stdin stängd
                    time.sleep(0.1)
                    continue
                kommando = rad.rstrip("\n").rstrip("\r")
                if kommando:
                    _tangent_kö.put(kommando)
                else:
                    # Tom rad = Enter
                    _tangent_kö.put("")
            except (EOFError, OSError):
                time.sleep(0.1)

    tråd = threading.Thread(target=lyssna, daemon=True)
    tråd.start()


# ============================================================
# Input från kön (ersätter input())
# ============================================================

def input_från_fifo(prompt=""):
    """
    Ersätter input(). Väntar på ett kommando från kön (antingen FIFO eller
    tangentbord) och returnerar det.

    Om FIFO:n inte är aktiv startas tangentbords-lyssnaren så att tangentbordet
    fortfarande fungerar.
    """
    global _tangentbord_aktiv

    if prompt:
        print(prompt, end="", flush=True)

    # Starta tangentbords-lyssnaren om den inte redan körs
    if not _tangentbord_aktiv:
        _starta_tangentbords_lyssnare()

    # Vänta på ett kommando (blockerar tills det kommer)
    kommando = _tangent_kö.get()

    # Skriv ut en bekräftelse så användaren ser vad som hände
    print(f"[input] {kommando if kommando else '<Enter>'}")

    return kommando


# ============================================================
# Tangentläsning för cv2.waitKey()-loopar
# ============================================================

def läs_tangent_från_kö():
    """
    Returnerar ett kommando från kön om ett finns, annars None.
    Används i inspelnings- och analysloopar som komplement till cv2.waitKey().
    """
    try:
        return _tangent_kö.get_nowait()
    except queue.Empty:
        return None


# ============================================================
# Statusfil (terminal → GUI)
# ============================================================

_status_skrivning_pågår = False


def skriv_status(läge, **data):
    """
    Skriver status till /tmp/jacktime_status.json.
    GUI:t läser denna fil för att visa rätt knappar och information.

    Exempel:
        skriv_status("huvudmeny")
        skriv_status("spelar_in", tid=23.4, frames=1400)
        skriv_status("analys_hund", hund=1, frame=1240, total_frames=5000)
    """
    global _status_skrivning_pågår

    if _status_skrivning_pågår:
        return
    _status_skrivning_pågår = True

    try:
        innehåll = {"läge": läge, "tidpunkt": time.time()}
        innehåll.update(data)

        temp_path = STATUS_PATH + ".tmp"
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump(innehåll, f, ensure_ascii=False)
        os.replace(temp_path, STATUS_PATH)
    except Exception:
        pass
    finally:
        _status_skrivning_pågår = False


def rensa_status():
    """Tar bort statusfilen (anropas vid avslut)."""
    if os.path.exists(STATUS_PATH):
        try:
            os.remove(STATUS_PATH)
        except OSError:
            pass
