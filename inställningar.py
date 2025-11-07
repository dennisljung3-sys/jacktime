from paths import relativ_sökväg
import cv2
import serial.tools.list_ports
import json
import os
import time
import platform
from textutils import ersätt_svenska_tecken

CONFIGFIL = relativ_sökväg("data/config.json")

def verifiera_faktisk_fps(index, fps_val, mätningssekunder=3):
    cap = cv2.VideoCapture(index)
    cap.set(cv2.CAP_PROP_FPS, fps_val)

    print(f"\n🧪 Mäter faktisk FPS under {mätningssekunder} sekunder...")
    start = time.time()
    räknare = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa bild.")
            break
        räknare += 1
        if time.time() - start >= mätningssekunder:
            break

    cap.release()
    faktisk_fps = räknare / mätningssekunder
    print(f"📊 Faktisk FPS: {faktisk_fps:.2f} (begärt: {fps_val})")
    return round(faktisk_fps, 2)

def välj_kamera_med_förhandsvisning():
    print("\n🔍 Söker efter tillgängliga kameror...")
    tillgängliga = []

    for index in range(5):
        if platform.system() == "Windows":
            cap = cv2.VideoCapture(index, cv2.CAP_DSHOW)
        else:
            cap = cv2.VideoCapture(index)

        if cap.isOpened():
            ret, frame = cap.read()
            if ret:
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                tillgängliga.append((index, w, h))
        cap.release()

    if not tillgängliga:
        print("❌ Inga kameror hittades.")
        return None, None, None

    print("\n📋 Tillgängliga kameror:")
    for i, (index, w, h) in enumerate(tillgängliga, start=1):
        print(f"{i}. Index {index} – {w}x{h}")

    while True:
        try:
            val = int(input("👉 Välj kamera (nummer): "))
            if 1 <= val <= len(tillgängliga):
                valt_index = tillgängliga[val - 1][0]
                break
        except ValueError:
            pass
        print("❌ Ogiltigt val. Försök igen.")

    print("\n🎞️ Välj önskad bildfrekvens (FPS):")
    print("1. 30 fps")
    print("2. 60 fps")
    print("3. 100 fps")
    print("4. 120 fps")
    fps_val = None
    while True:
        val = input("👉 Välj (1–4): ").strip()
        if val == "1":
            fps_val = 30
            break
        elif val == "2":
            fps_val = 60
            break
        elif val == "3":
            fps_val = 100
            break
        elif val == "4":
            fps_val = 120
            break
        else:
            print("❌ Ogiltigt val. Försök igen.")

    if platform.system() == "Windows":
        cap = cv2.VideoCapture(valt_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(valt_index)
    cap.set(cv2.CAP_PROP_FPS, fps_val)
    verifierad_fps = cap.get(cv2.CAP_PROP_FPS)
    print(f"📡 Begärd FPS: {fps_val} – Kameran rapporterar: {verifierad_fps:.1f} fps")

    print("\n📺 Visar live-feed från vald kamera. Tryck 'q' för att bekräfta, eller vänta 10 sekunder.")
    cv2.namedWindow("Förhandsvisning", cv2.WINDOW_NORMAL)

# 📐 Skärmstorlek och fönsterplacering
    screen_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH)) * 2  # fallback om Tkinter inte funkar
    screen_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT)) * 2

    try:
        import tkinter as tk
        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
    except:
        pass  # fallback används

    fönster_bredd = screen_width // 2
    fönster_höjd = screen_height // 2
    x_pos = screen_width // 2
    y_pos = 0

    cv2.resizeWindow("Förhandsvisning", fönster_bredd, fönster_höjd)
    cv2.moveWindow("Förhandsvisning", x_pos, y_pos)

    start_tid = time.time()
    confirmed = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa bild från kameran.")
            break
        cv2.imshow("Förhandsvisning", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            confirmed = True
            break
        if time.time() - start_tid > 10:
            break

    cv2.destroyAllWindows()
    cap.release()

    if confirmed:
        faktisk_fps = verifiera_faktisk_fps(valt_index, fps_val)
        return valt_index, fps_val, faktisk_fps
    else:
        svar = input("✅ Är detta rätt kamera? (j/n): ").strip().lower()
        if svar == "j":
            faktisk_fps = verifiera_faktisk_fps(valt_index, fps_val)
            return valt_index, fps_val, faktisk_fps
        else:
            print("🔁 Välj en annan kamera.")
            return välj_kamera_med_förhandsvisning()

def välj_arduino_port():
    print("\n🔌 Söker efter inkopplade Arduino-enheter...")
    portar = list(serial.tools.list_ports.comports())
    if not portar:
        print("❌ Inga Arduino-enheter hittades.")
        return None

    for i, port in enumerate(portar, start=1):
        print(f"{i}. {port.device} – {port.description}")
    while True:
        try:
            val = int(input("👉 Välj Arduino-port (nummer): "))
            if 1 <= val <= len(portar):
                return portar[val - 1].device
        except ValueError:
            pass
        print("❌ Ogiltigt val. Försök igen.")

def ändra_inställningar(config):
    kamera_index, kamera_fps, verifierad_fps = välj_kamera_med_förhandsvisning()
    if kamera_index is None:
        print("❌ Ingen kamera valdes.")
        return

    arduino_port = välj_arduino_port()
    if arduino_port is None:
        print("❌ Ingen Arduino valdes.")
        return

    config["kamera_index"] = kamera_index
    config["kamera_fps"] = kamera_fps
    config["verifierad_fps"] = verifierad_fps
    config["arduino_port"] = arduino_port
    with open(CONFIGFIL, "w") as f:
        json.dump(config, f, indent=2)
    print(f"\n💾 Inställningar sparade:")
    print(f"  Kamera-index: {kamera_index}")
    print(f"  Begärd FPS: {kamera_fps}")
    print(f"  Verifierad FPS: {verifierad_fps}")
    print(f"  Arduino-port: {arduino_port}")
