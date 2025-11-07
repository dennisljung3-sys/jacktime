import serial
import time
import threading
import platform

if platform.system() == "Windows":
    import msvcrt
else:
    import sys
    import select

def vänta_på_startsignal(arduino_port):
    """
    Väntar på startsignal från Arduino eller tryck på Enter.
    ESC avbryter och återgår till huvudmenyn.
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

    def lyssna_tangentbord():
        if platform.system() == "Windows":
            print("🟡 Tryck [Enter] för manuell start eller [ESC] för att avbryta...")
            while starttid[0] is None and not avbruten[0]:
                if msvcrt.kbhit():
                    key = msvcrt.getch()
                    if key in [b'\r', b'\n']:
                        starttid[0] = time.time()
                        print("✅ Startsignal manuellt via tangentbord.")
                        break
                    elif key == b'\x1b':  # ESC
                        avbruten[0] = True
                        print("↩️ Avbrutet – återgår till huvudmenyn.")
                        break
        else:
            print("🟡 Tryck [Enter] för manuell start eller [ESC] + [Enter] för att avbryta...")
            while starttid[0] is None and not avbruten[0]:
                i, _, _ = select.select([sys.stdin], [], [], 0.1)
                if i:
                    rad = sys.stdin.readline().strip().lower()
                    if rad == "":
                        starttid[0] = time.time()
                        print("✅ Startsignal manuellt via tangentbord.")
                        break
                    elif rad == "esc":
                        avbruten[0] = True
                        print("↩️ Avbrutet – återgår till huvudmenyn.")
                        break

    # Starta båda lyssnarna parallellt
    tråd_arduino = threading.Thread(target=lyssna_arduino, daemon=True)
    tråd_tangent = threading.Thread(target=lyssna_tangentbord, daemon=True)
    tråd_arduino.start()
    tråd_tangent.start()

    # Vänta tills något händer
    while starttid[0] is None and not avbruten[0]:
        time.sleep(0.001)

    if avbruten[0]:
        return None
    return starttid[0]
