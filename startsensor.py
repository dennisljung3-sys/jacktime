# startsensor.py
import serial
import time
import threading
from fifo_input import läs_tangent_från_kö, skriv_status


def vänta_på_startsignal(arduino_port):
    """
    Väntar på startsignal från Arduino eller Enter (från FIFO eller tangentbord).
    'esc' (från FIFO eller tangentbord) avbryter.

    Arduino-lyssnaren körs i en egen tråd och påverkas inte av kö-lyssnaren.
    Tidstämpeln sätts direkt när Arduino-signalen tas emot – ingen kö emellan.
    """
    starttid = [None]
    avbruten = [False]

    def lyssna_arduino():
        try:
            ser = serial.Serial(arduino_port, 9600, timeout=0.01)
            while starttid[0] is None and not avbruten[0]:
                rad = ser.readline().decode(errors="ignore").strip()
                if "start" in rad.lower():
                    starttid[0] = time.time()
                    print("✅ Startsignal från Arduino!")
                    break
        except serial.SerialException:
            print("⚠️ Kunde inte öppna Arduino-porten.")

    def lyssna_kö():
        """Läser kommandon från kön (FIFO eller tangentbord)."""
        while starttid[0] is None and not avbruten[0]:
            kommando = läs_tangent_från_kö()
            if kommando is None:
                time.sleep(0.02)  # 20 ms paus mellan kontroller
                continue

            kommando_lower = kommando.strip().lower()

            # Tom sträng = Enter
            if kommando_lower == "":
                starttid[0] = time.time()
                print("✅ Startsignal manuellt (Enter).")
                break
            elif kommando_lower == "esc":
                avbruten[0] = True
                print("↩️ Avbrutet – återgår till huvudmenyn.")
                break
            else:
                # Okänt kommando – ignorera men skriv ut för felsökning
                print(f"ℹ️ Ignorerar kommando under väntan på start: '{kommando}'")

    # Skriv status så GUI:t vet att vi väntar
    skriv_status(
        "vantar_start",
        meddelande="Väntar på startsignal (Arduino eller Enter)",
    )

    # Starta båda lyssnarna parallellt
    tråd_arduino = threading.Thread(target=lyssna_arduino, daemon=True)
    tråd_kö = threading.Thread(target=lyssna_kö, daemon=True)
    tråd_arduino.start()
    tråd_kö.start()

    # Vänta tills något händer
    while starttid[0] is None and not avbruten[0]:
        time.sleep(0.001)

    if avbruten[0]:
        return None
    return starttid[0]
