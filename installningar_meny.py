# installningar_meny.py - FULLSTÄNDIG version
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
        print(f"3. Sätt mållinje (nu: {config.get('mållinje_x')})")
        print("4. Kalibrera kamera")
        print("5. Visa aktuell konfiguration")
        print("6. Tillbaka till huvudmenyn")
        val = input("👉 Välj (1–6): ").strip()

        if val == "1":
            andra_kamera(config)
        elif val == "2":
            andra_arduino(config)
        elif val == "3":
            sätt_mållinje(config)
        elif val == "4":
            kalibrera_kamera()
        elif val == "5":
            visa_konfiguration(config)
        elif val == "6":
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
    original_höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
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

        # ⭐ ROTERA BILDEN 90° MOTURS
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Hämta nya dimensioner (behövs för textpositioner)
        höjd, bredd = frame.shape[:2]

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


def sätt_mållinje(config):
    """Sätter mållinjen och sparar i config"""
    print("\n📍 Sätter mållinje...")

    # Hämta fönsterhanteraren
    from fönsterhanterare import get_fönster

    fönster = get_fönster()

    if fönster is None:
        print("❌ Fönsterhanteraren är inte tillgänglig!")
        return

    # Kontrollera att kamera är vald
    kamera_index = config.get("kamera_index")
    if kamera_index is None:
        print("❌ Välj kamera först! (Inställningar → Andra kamera)")
        return

    # Koppla kameran
    if not fönster.koppla_kamera(kamera_index):
        print("❌ Kunde inte öppna kameran.")
        return

    # Hämta kamerainställningar
    cap = fönster.cap
    original_höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    # Efter rotation kommer höjd och bredd att byta plats
    print(f"📷 Kamera ansluten: {original_bredd}x{original_höjd}")

    # Hämta sparad mållinje (om den finns)
    mållinje_x = config.get("mållinje_x")
    if mållinje_x is not None:
        print(f"📌 Sparad mållinje: x = {mållinje_x}")
        print("   Tryck ENTER för att använda sparad, eller A/D/klicka för att justera")
    else:
        print("📍 Ingen sparad mållinje - ställ in nu")

    # Variabler
    mållinje_ändrad = False
    bekräftad = False

    # Byt läge till förhandsvisning
    fönster.byt_läge("förhandsvisning")

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        # ⭐ ROTERA BILDEN 90° MOTURS
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # ⭐ HÄMTA NYA DIMENSIONER EFTER ROTATION
        höjd, bredd = frame.shape[:2]

        visning = frame.copy()

        # Rita mållinje
        if mållinje_x is not None:
            cv2.line(visning, (mållinje_x, 0), (mållinje_x, höjd), (0, 0, 255), 3)
            if not mållinje_ändrad:
                cv2.putText(
                    visning,
                    "SPARAD MALLINJE (röd) - Tryck ENTER för att använda",
                    (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    0.6,
                    (0, 0, 255),
                    2,
                )
        else:
            # Temporär mållinje i mitten (grå)
            mitt_x = bredd // 2
            cv2.line(visning, (mitt_x, 0), (mitt_x, höjd), (100, 100, 100), 2)
            cv2.putText(
                visning,
                "TEMP MALLINJE - Klicka eller A/D för att flytta",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (150, 150, 150),
                2,
            )

        # Instruktioner
        cv2.putText(
            visning,
            "A/D = flytta linje, ENTER = spara, Q = avbryt",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Position
        if mållinje_x is not None:
            pos_text = f"Position: {mållinje_x}" + (
                " (justerad)" if mållinje_ändrad else " (sparad)"
            )
            cv2.putText(
                visning,
                pos_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
            )

        cv2.imshow(fönster.fönster_namn, visning)
        tangent = cv2.waitKey(1) & 0xFF

        if tangent == ord("\r") or tangent == ord("\n"):  # Enter
            if mållinje_x is not None:
                bekräftad = True
                break
            else:
                print("⚠️ Sätt en mållinje först (klicka eller A/D)")
        elif tangent == ord("q"):
            print("❌ Avbröt.")
            break
        elif tangent == ord("a"):
            if mållinje_x is None:
                mållinje_x = bredd // 2
            mållinje_x = max(0, mållinje_x - 10)
            mållinje_ändrad = True
            print(f"📍 Mållinje flyttad till x = {mållinje_x}")
        elif tangent == ord("d"):
            if mållinje_x is None:
                mållinje_x = bredd // 2
            mållinje_x = min(bredd, mållinje_x + 10)
            mållinje_ändrad = True
            print(f"📍 Mållinje flyttad till x = {mållinje_x}")

    # Koppla från kameran
    fönster.koppla_från_kamera()
    fönster.byt_läge("tom")
    fönster.visa_startsida()

    # Spara om bekräftad
    if bekräftad and mållinje_x is not None:
        config["mållinje_x"] = mållinje_x
        spara_config(config)
        print(f"💾 Mållinje sparad: x = {mållinje_x}")
    else:
        print("❌ Ingen mållinje sparades.")


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
