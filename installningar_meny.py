import os
import json
import platform
import time
import cv2
import serial.tools.list_ports
from paths import relativ_sökväg

CONFIGFIL = relativ_sökväg("data/config.json")
LATENSFIL = relativ_sökväg("data/latens_config.json")

def las_config():
    if not os.path.exists(CONFIGFIL):
        return {}
    with open(CONFIGFIL, "r") as f:
        return json.load(f)

def spara_config(config):
    os.makedirs(os.path.dirname(CONFIGFIL), exist_ok=True)
    with open(CONFIGFIL, "w") as f:
        json.dump(config, f, indent=2)

def installningsmeny():
    while True:
        config = las_config()
        print("\n⚙️ INSTÄLLNINGAR")
        print(f"1. Andra kamera och FPS (nu: index {config.get('kamera_index')} @ {config.get('kamera_fps')} FPS)")
        print(f"2. Andra Arduino-port (nu: {config.get('arduino_port')})")
        print("3. Kalibrera kamera")
        print("4. Visa aktuell konfiguration")
        print("5. Tillbaka till huvudmenyn")
        val = input("👉 Välj (1–5): ").strip()

        if val == "1":
            andra_kamera(config)
        elif val == "2":
            andra_arduino(config)
        elif val == "3":
            kalibrera_kamera()
        elif val == "4":
            visa_konfiguration(config)
        elif val == "5":
            break
        else:
            print("❌ Ogiltigt val. Försök igen.")

def andra_kamera(config):
    print("\n🎥 Väljer ny kamera och FPS...")
    tillgängliga = []
    for i in range(5):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            tillgängliga.append((i, w, h, fps))
            cap.release()

    if not tillgängliga:
        print("❌ Inga kameror hittades.")
        return

    print("\n📋 Tillgängliga kameror:")
    for i, (index, w, h, fps) in enumerate(tillgängliga, start=1):
        print(f"{i}. Index {index} – {w}x{h} @ {int(fps)} FPS")

    while True:
        val = input("👉 Välj kamera (nummer): ").strip()
        if val.isdigit() and 1 <= int(val) <= len(tillgängliga):
            valt_index = tillgängliga[int(val) - 1][0]
            break
        print("❌ Ogiltigt val.")

    print("\n🎞️ Välj önskad FPS:")
    print("1. 30 fps\n2. 60 fps\n3. 100 fps\n4. 120 fps")
    fps_dict = {"1": 30, "2": 60, "3": 100, "4": 120}
    while True:
        val = input("👉 Välj (1–4): ").strip()
        if val in fps_dict:
            fps_val = fps_dict[val]
            break
        print("❌ Ogiltigt val.")

    cap = cv2.VideoCapture(valt_index)
    cap.set(cv2.CAP_PROP_FPS, fps_val)
    verifierad_fps = cap.get(cv2.CAP_PROP_FPS)
    cap.release()

    config["kamera_index"] = valt_index
    config["kamera_fps"] = fps_val
    config["verifierad_fps"] = round(verifierad_fps, 2)
    spara_config(config)
    print(f"\n💾 Kamera-inställningar sparade: index {valt_index}, FPS {fps_val} (verifierad: {verifierad_fps:.2f})")

def andra_arduino(config):
    print("\n🔌 Söker efter Arduino-enheter...")
    portar = list(serial.tools.list_ports.comports())
    if not portar:
        print("❌ Inga enheter hittades.")
        return

    for i, port in enumerate(portar, start=1):
        print(f"{i}. {port.device} – {port.description}")
    while True:
        val = input("👉 Välj port (nummer): ").strip()
        if val.isdigit() and 1 <= int(val) <= len(portar):
            vald_port = portar[int(val) - 1].device
            break
        print("❌ Ogiltigt val.")

    config["arduino_port"] = vald_port
    spara_config(config)
    print(f"\n💾 Arduino-port sparad: {vald_port}")

def kalibrera_kamera():
    print("\n📡 Startar kalibrering...")
    try:
        import kalibrera_kamera
        kamera_index, fps = las_config().get("kamera_index"), las_config().get("kamera_fps")
        if kamera_index is None or fps is None:
            print("⚠️ Kamera måste väljas först.")
            return
        kalibrera_kamera.kör_kalibrering(kamera_index, fps)
    except Exception as e:
        print(f"❌ Fel vid kalibrering: {e}")

def visa_konfiguration(config):
    print("\n📦 Aktuell konfiguration:")
    for nyckel, värde in config.items():
        print(f"  {nyckel}: {värde}")
    if os.path.exists(LATENSFIL):
        with open(LATENSFIL, "r") as f:
            latensdata = json.load(f)
        print("\n📈 Kalibrerad latensdata:")
        for nyckel, värde in latensdata.items():
            print(f"  {nyckel}: {värde}")
