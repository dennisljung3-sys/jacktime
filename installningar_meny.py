# installningar_meny.py
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
        print(
            f"1. Andra kamera och FPS (nu: index {config.get('kamera_index')} @ {config.get('kamera_fps')} FPS)"
        )
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

    # Först, lista alla kameror
    for i in range(10):
        cap = cv2.VideoCapture(i)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            tillgängliga.append({"index": i, "w": w, "h": h, "fps": fps})
            cap.release()

    if not tillgängliga:
        print("❌ Inga kameror hittades.")
        return

    print("\n📋 Tillgängliga kameror:")
    for i, cam in enumerate(tillgängliga, start=1):
        print(
            f"{i}. Index {cam['index']} – {cam['w']}x{cam['h']} @ {int(cam['fps'])} FPS"
        )

    # Välj kamera
    while True:
        val = input("👉 Välj kamera (nummer): ").strip()
        if val.isdigit() and 1 <= int(val) <= len(tillgängliga):
            valt_index = tillgängliga[int(val) - 1]["index"]
            break
        print("❌ Ogiltigt val.")

    # Hämta fönsterhanteraren
    from fönsterhanterare import get_fönster

    fönster = get_fönster()

    if fönster is None:
        print("❌ Fönsterhanteraren är inte tillgänglig!")
        return

    # Anslut kameran via fönsterhanteraren
    if not fönster.koppla_kamera(valt_index):
        print("❌ Kunde inte öppna kameran.")
        return

    # Hämta kamerainställningar
    cap = fönster.cap
    höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    verifierad_fps = cap.get(cv2.CAP_PROP_FPS)

    print(f"\n📺 Visar live-feed från kamera {valt_index} i JackTime-fönstret.")
    print("   Tryck 'q' för att bekräfta, ESC för att avbryta.")

    # Spara referens till gammalt läge
    gammalt_läge = fönster.nuvarande_läge

    # Byt läge till förhandsvisning
    fönster.byt_läge("förhandsvisning")

    bekräftad = False

    # Huvudloop för förhandsvisning
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        # Skapa en kopia för visning
        visning = frame.copy()

        # Visa information på bilden
        info_text = f"Kamera {valt_index} | Tryck Q for att bekrafta, ESC for avbryt"
        cv2.putText(
            visning, info_text, (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2
        )

        # Visa FPS
        cv2.putText(
            visning,
            f"FPS: {verifierad_fps:.1f}",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Visa i fönsterhanteraren
        cv2.imshow(fönster.fönster_namn, visning)

        # Hantera tangentbord
        tangent = cv2.waitKey(1) & 0xFF

        if tangent == ord("q"):
            bekräftad = True
            break
        elif tangent == 27:  # ESC
            print("❌ Avbröt kameraval.")
            break

    # Koppla från kameran (temporärt)
    fönster.koppla_från_kamera()

    # Återställ till tidigare läge
    fönster.byt_läge(gammalt_läge)

    # Visa startsidan igen om vi var i tom-läge
    if gammalt_läge == "tom":
        fönster.visa_startsida()

    if not bekräftad:
        return

    # Fråga om FPS
    print("\n🎞️ Välj önskad FPS:")
    print("1. 30 fps\n2. 60 fps\n3. 100 fps\n4. 120 fps")
    fps_dict = {"1": 30, "2": 60, "3": 100, "4": 120}
    while True:
        val = input("👉 Välj (1–4): ").strip()
        if val in fps_dict:
            fps_val = fps_dict[val]
            break
        print("❌ Ogiltigt val.")

    # Verifiera faktisk FPS (med tillfällig kamera)
    test_cap = cv2.VideoCapture(valt_index)
    test_cap.set(cv2.CAP_PROP_FPS, fps_val)
    verifierad_fps = test_cap.get(cv2.CAP_PROP_FPS)
    test_cap.release()

    # Spara inställningar
    config["kamera_index"] = valt_index
    config["kamera_fps"] = fps_val
    config["verifierad_fps"] = round(verifierad_fps, 2)
    spara_config(config)

    print(
        f"\n💾 Kamera-inställningar sparade: index {valt_index}, FPS {fps_val} (verifierad: {verifierad_fps:.2f})"
    )


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

        config = las_config()
        kamera_index = config.get("kamera_index")
        fps = config.get("kamera_fps")
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
