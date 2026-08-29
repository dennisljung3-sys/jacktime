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
    Förbereder kameran och visar förhandsvisning med sparad mållinje.
    """
    # Hämta sparad mållinje från config
    mållinje_x = config.get("mållinje_x")
    if mållinje_x is None:
        print("⚠️ Ingen mållinje sparad! Gå till Inställningar → Sätt mållinje först.")
        # Använd mitten som fallback (sätts senare när vi har bredden)
        mållinje_x = 320

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

    # Hämta original dimensioner
    original_höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    original_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    print(
        f"📷 Kamera ansluten: {original_bredd}x{original_höjd} @ {verifierad_fps:.1f} FPS"
    )
    print(f"📍 Mållinje: x = {mållinje_x}")
    print("   Tryck ENTER för att starta tidtagning, eller Q för att avbryta")

    # Byt läge till tidtagning
    fönster.byt_läge("tidtagning", mållinje_x=mållinje_x)

    # Visa förhandsvisning tills användaren är redo
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        # ⭐ ROTERA BILDEN 90° MOTURS
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # ⭐ HÄMTA NYA DIMENSIONER EFTER ROTATION
        höjd, bredd = frame.shape[:2]

        # Skapa en kopia för visning
        visning = frame.copy()

        # Rita mållinje i GRÖNT (visar att den är sparad)
        # Använd mållinje_x från config (sparad i original koordinater)
        # Efter rotation är x-koordinaten densamma, men höjden har ändrats
        cv2.line(visning, (mållinje_x, 0), (mållinje_x, höjd), (0, 255, 0), 3)

        cv2.putText(
            visning,
            "SPARAD MALLINJE (grön)",
            (10, 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (0, 255, 0),
            2,
        )
        cv2.putText(
            visning,
            "Tryck ENTER för att börja tidtagning, Q för att avbryta",
            (10, 60),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (255, 255, 255),
            2,
        )

        cv2.imshow(fönster.fönster_namn, visning)
        tangent = cv2.waitKey(1) & 0xFF

        if tangent == ord("\r") or tangent == ord("\n"):  # Enter
            break
        elif tangent == ord("q"):
            print("❌ Avbröt.")
            fönster.koppla_från_kamera()
            fönster.byt_läge("tom")
            fönster.visa_startsida()
            return None, {}

    # Hämta skärmstorlek för metadata
    screen_width, screen_height = hämta_skärmstorlek()

    metadata = {
        "mållinje_x": mållinje_x,
        "skärmstorlek": (screen_width, screen_height),
        "kamera_index": kamera_index,
        "fps": verifierad_fps,
    }

    return cap, metadata
