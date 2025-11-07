import cv2
import numpy as np
import time
import json
import statistics
import os
from datetime import datetime
from paths import relativ_sökväg

# === Inställningar ===
BLINK_FREKVENS_HZ = 4
BLINK_INTERVAL = 1 / BLINK_FREKVENS_HZ
ANTAL_BLINKNINGAR = 20
MAX_LATENS_MS = 300
SKÄRM_LATENS_MS = 20
ROI = (0.45, 0.45, 0.1, 0.1)  # x, y, w, h i procent

def kör_kalibrering(kamera_index, önskad_fps):
    cap = cv2.VideoCapture(kamera_index)
    cap.set(cv2.CAP_PROP_FPS, önskad_fps)
    if not cap.isOpened():
        print("❌ Kunde inte öppna kameran.")
        return

    fps_mätningar = []
    latens_mätningar = []
    missade = 0
    skärm_tider = []
    färg = 0

    cv2.namedWindow("Kalibrering", cv2.WINDOW_NORMAL)
    cv2.setWindowProperty("Kalibrering", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN)

    print("🟡 Rikta kameran mot skärmen...")
    time.sleep(2)
    print("✅ Startar blinkning...")

    senaste_blink = time.time()
    frame_count = 0
    fps_start = time.time()
    senaste_färg = färg
    senaste_skärmtid = senaste_blink
    registrerade = 0

    while registrerade < ANTAL_BLINKNINGAR:
        nu = time.time()
        if nu - senaste_blink >= BLINK_INTERVAL:
            färg = 255 if färg == 0 else 0
            senaste_blink = nu
            skärm_tider.append(nu)
            senaste_färg = färg
            senaste_skärmtid = nu

        bild = np.full((600, 800, 3), färg, dtype=np.uint8)

        # Lägg till overlay-text
        cv2.putText(bild, "Q om du vill avbryta", (10, 580),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 255), 2)

        cv2.imshow("Kalibrering", bild)


        ret, frame = cap.read()
        if not ret:
            continue

        frame_count += 1
        if time.time() - fps_start >= 1.0:
            fps_mätningar.append(frame_count)
            frame_count = 0
            fps_start = time.time()

        h, w, _ = frame.shape
        x, y, rw, rh = ROI
        roi = frame[int(y*h):int((y+y*h)*h), int(x*w):int((x+rw)*w)]
        medelvärde = np.mean(roi)

        if senaste_färg == 255 and medelvärde > 200:
            latens = (nu - senaste_skärmtid) * 1000
            if 0 < latens < MAX_LATENS_MS:
                latens_mätningar.append(latens)
                registrerade += 1
                senaste_färg = 0
            else:
                missade += 1

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

    medel_latens = round(statistics.mean(latens_mätningar), 2) if latens_mätningar else None
    std_latens = round(statistics.stdev(latens_mätningar), 2) if len(latens_mätningar) > 1 else 0
    medel_fps = round(statistics.mean(fps_mätningar), 2) if fps_mätningar else 0
    std_fps = round(statistics.stdev(fps_mätningar), 2) if len(fps_mätningar) > 1 else 0

    frame_intervall_ms = 1000 / medel_fps if medel_fps else 0
    fps_variation_span = round(frame_intervall_ms / 2, 1)
    andel_fps_variation = min(1.0, fps_variation_span / std_latens) if std_latens > 0 else 0
    procentandel = round(andel_fps_variation * 100)

    justerad_latens = round(medel_latens - SKÄRM_LATENS_MS, 2) if medel_latens else None

    # Skriv ut sammanfattning
    print(f"""
📅 Kalibrering klar!
🎥 Kamera: index {kamera_index}
🎯 Begärd FPS: {önskad_fps}
📡 Faktisk FPS: {medel_fps} ± {std_fps}
⚡ Blinkningar: {ANTAL_BLINKNINGAR}, Registrerade: {len(latens_mätningar)}, Missade: {missade}
📈 Latens: {medel_latens} ms ± {std_latens} ms
📉 Uppskattad FPS-bidrag till latensvariation: ~{fps_variation_span} ms (vid {medel_fps} FPS)
📊 Uppskattad andel av latensvariation som kan bero på FPS: ~{procentandel}%
📺 Antagen skärmlatens: {SKÄRM_LATENS_MS} ms
📈 Justerad systemlatens (exkl. skärm): {justerad_latens} ms
""")

    # Spara endast relevant data
    os.makedirs("data", exist_ok=True)
    with open("data/latens_config.json", "w") as f:
        json.dump({
            "justerad_latens_ms": justerad_latens,
            "fps": medel_fps,
            "fps_std": std_fps,
            "fps_variation_span_ms": fps_variation_span,
            "fps_variation_procent": procentandel,
            "skärm_latens_ms": SKÄRM_LATENS_MS
        }, f, indent=2)

    print("💾 Kalibrering sparad i data/latens_config.json")

# === Direktkörning (valfritt)
if __name__ == "__main__":
    with open(relativ_sökväg("data", "config.json")) as f:
        config = json.load(f)

    kamera_index = config.get("kamera_index")
    önskad_fps = config.get("kamera_fps")

    if kamera_index is None or önskad_fps is None:
        print("⚠️ Kamera måste väljas först i inställningsmenyn.")
    else:
        kör_kalibrering(kamera_index, önskad_fps)
        print("✅ Kalibrering avslutad.")
