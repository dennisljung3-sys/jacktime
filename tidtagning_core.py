# tidtagning_core.py (uppdaterad version)
import cv2
import platform
import tkinter as tk
from textutils import ersätt_svenska_tecken
from fönsterhanterare import get_fönster
from confighantering import spara_config


def hämta_skärmstorlek():
    """Hämtar skärmstorlek för att kunna placera fönster"""
    try:
        root = tk.Tk()
        root.withdraw()
        return root.winfo_screenwidth(), root.winfo_screenheight()
    except:
        return 1920, 1080  # Fallback


def rita_overlay(frame, mållinje_x=None, tid_str=None):
    """Ritar mållinje och tid på en frame"""
    höjd, bredd = frame.shape[:2]
    x = mållinje_x if mållinje_x is not None else bredd // 2
    cv2.line(frame, (x, 0), (x, höjd), (0, 0, 255), 2)
    if tid_str:
        tid_str = ersätt_svenska_tecken(tid_str)
        cv2.putText(
            frame, tid_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2
        )
    return frame


def förbered_kamera_och_mållinje(config):
    """
    Förbereder kameran och låter användaren sätta mållinjen.
    Sparar mållinjen i config så att den kommer ihåg till nästa gång.
    """
    # Hämta sparad mållinje från config (om den finns)
    mållinje_x = config.get("mållinje_x")
    if mållinje_x is not None:
        print(f"📌 Sparad mållinje hittades: x = {mållinje_x}")
        print("   Tryck ENTER for att använda sparad, eller A/D/klicka for att justera")
    else:
        print("📍 Ingen sparad mållinje - ställ in nu")

    # Hämta fönsterhanteraren
    fönster = get_fönster()
    if fönster is None:
        print("❌ Fönsterhanteraren är inte tillgänglig!")
        return None, {}

    # Koppla kameran via fönsterhanteraren
    kamera_index = config.get("kamera_index")
    if kamera_index is None:
        print("❌ Ingen kamera vald. Gå till inställningar först.")
        return None, {}

    if not fönster.koppla_kamera(kamera_index):
        print("❌ Kunde inte öppna kameran.")
        return None, {}

    # Hämta kamerainställningar
    cap = fönster.cap
    fps = config.get("kamera_fps", 30)
    verifierad_fps = cap.get(cv2.CAP_PROP_FPS)
    config["verifierad_fps"] = verifierad_fps

    höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    print(f"📷 Kamera ansluten: {bredd}x{höjd} @ {verifierad_fps:.1f} FPS")

    # Variabel för att hålla reda på om användaren ändrat mållinjen
    mållinje_ändrad = False
    använd_sparad = True

    # Huvudloop för att sätta/justera mållinjen
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        # Skapa en kopia för visning
        visning = frame.copy()

        # Bestäm vilken mållinje som ska visas
        if mållinje_ändrad or mållinje_x is None:
            # Använd den justerade eller nya mållinjen
            visa_x = mållinje_x if mållinje_x is not None else bredd // 2
            cv2.line(visning, (visa_x, 0), (visa_x, höjd), (0, 0, 255), 3)
        else:
            # Visa sparad mållinje i grönt
            cv2.line(visning, (mållinje_x, 0), (mållinje_x, höjd), (0, 255, 0), 3)

        # Visa instruktioner på bilden
        if mållinje_x is not None and not mållinje_ändrad:
            cv2.putText(
                visning,
                "SPARAD MALLINJE (gron) - Tryck ENTER for att anvanda",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        cv2.putText(
            visning,
            "Klicka eller A/D = justera, ENTER = bekrafta, Q = avbryt",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        # Visa nuvarande position
        if mållinje_x is not None:
            pos_text = f"Position: {mållinje_x}"
            if not mållinje_ändrad and mållinje_x is not None:
                pos_text += " (sparad)"
            cv2.putText(
                visning,
                pos_text,
                (10, 90),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (200, 200, 200),
                1,
            )

        # Visa i fönsterhanteraren
        cv2.imshow(fönster.fönster_namn, visning)

        # Hantera tangentbord
        tangent = cv2.waitKey(1) & 0xFF

        if tangent == ord("\r") or tangent == ord("\n"):  # Enter
            # Bekräfta nuvarande mållinje
            if mållinje_x is None:
                mållinje_x = bredd // 2
            break
        elif tangent == ord("q"):
            # Avbryt - använd mitten som fallback
            mållinje_x = bredd // 2
            print("ℹ️ Avbröt - använder mitten som mållinje")
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

    # Om ingen mållinje sattes, använd mitten
    if mållinje_x is None:
        mållinje_x = bredd // 2

    # Spara mållinjen i config (om den ändrades eller är ny)
    if mållinje_ändrad or config.get("mållinje_x") != mållinje_x:
        config["mållinje_x"] = mållinje_x
        spara_config(config)
        print(f"💾 Mållinje sparad: {mållinje_x}")
    else:
        print(f"✅ Använder sparad mållinje: {mållinje_x}")

    # Hämta skärmstorlek för metadata
    screen_width, screen_height = hämta_skärmstorlek()

    metadata = {
        "mållinje_x": mållinje_x,
        "skärmstorlek": (screen_width, screen_height),
        "kamera_index": kamera_index,
        "fps": verifierad_fps,
    }

    # Returnera SAMMA cap som fönsterhanteraren använder
    return cap, metadata
