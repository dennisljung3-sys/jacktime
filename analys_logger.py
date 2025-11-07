import cv2
import os
import json
from datetime import datetime
from analys_overlay import rita_overlay
from paths import relativ_sökväg
from textutils import sanera_filnamn

def logga_tid(hundnummer, tid_före, tid_efter, före_pos, efter_pos, mållinje_x):
    if före_pos == efter_pos:
        print(f"⚠️ Hund {hundnummer}: nospositioner identiska – kan inte interpolera.")
        return None
    total_dx = efter_pos - före_pos
    mål_dx = mållinje_x - före_pos
    andel = mål_dx / total_dx
    tid_diff = tid_efter - tid_före
    passeringstid = tid_före + andel * tid_diff
    print(f"✅ Hund {hundnummer}: passerade vid {passeringstid:.3f} s")
    return round(passeringstid, 3)

def visa_loggningsstatus(loggade_tider, startlista):
    print("\n📋 Loggningsstatus:")
    for hundnummer in sorted(startlista.keys(), key=int):
        info = startlista[hundnummer]
        namn = info.get("namn", "Okänd")
        tider = loggade_tider.get(hundnummer, [])
        status = f"{len(tider)} tider" if tider else "❌"
        print(f"  Hund {hundnummer}: {namn} {status}")

def hantera_loggning(cap, metadata, startlista):
    fps = metadata.get("fps")
    if fps is None:
        try:
            with open(relativ_sökväg("data", "config.json")) as f:
                config = json.load(f)
            fps = config.get("verifierad_fps") or config.get("kamera_fps") or 30
            print(f"⚠️ Ingen FPS i metadata – använder fallback: {fps} FPS")
        except:
            fps = 30
            print("⚠️ Kunde inte läsa config – använder 30 FPS som fallback.")

    fördröjning = metadata.get("fördröjning", 0)
    frame_tider = metadata.get("frame_tider")
    ursprunglig_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    skärmstorlek = metadata.get("skärmstorlek", [1280, 720])
    fönster_bredd = skärmstorlek[0] // 2
    fönster_höjd = fönster_bredd * 9 // 16
    skal_x = ursprunglig_bredd / fönster_bredd
    mållinje_x = metadata.get("mållinje_x")
    mållinje_x_scaled = int(mållinje_x / skal_x) if mållinje_x else None

    cv2.namedWindow("Analys", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Analys", fönster_bredd, fönster_höjd)
    cv2.moveWindow("Analys", skärmstorlek[0] // 2, 0)

    loggade_tider = {str(nr): "DNF" for nr in startlista.keys()}
    frame_index = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    aktiv_hund = None
    klick_före = klick_efter = frame_före = frame_efter = aktuell_frame = None

    def klick(event, x, y, flags, param):
        nonlocal klick_före, klick_efter, frame_före, frame_efter, aktiv_hund
        if event == cv2.EVENT_LBUTTONDOWN and aktiv_hund:
            ursprunglig_x = int(x * skal_x)
            if klick_före is None:
                klick_före = ursprunglig_x
                frame_före = frame_index
                print(f"🐾 Hund {aktiv_hund}: nos före målgång markerad (frame {frame_före}, x={klick_före})")
            elif klick_efter is None:
                klick_efter = ursprunglig_x
                frame_efter = frame_index
                print(f"🐾 Hund {aktiv_hund}: nos efter målgång markerad (frame {frame_efter}, x={klick_efter})")
                if frame_tider and frame_före < len(frame_tider) and frame_efter < len(frame_tider):
                    tid_före = frame_tider[frame_före]
                    tid_efter = frame_tider[frame_efter]
                else:
                    tid_före = frame_före / fps + fördröjning
                    tid_efter = frame_efter / fps + fördröjning
                tid = logga_tid(aktiv_hund, tid_före, tid_efter, klick_före, klick_efter, mållinje_x)
                if tid is not None:
                    hund_id = str(aktiv_hund)
                    if hund_id not in loggade_tider:
                        loggade_tider[hund_id] = []
                    loggade_tider[hund_id] = [tid]
                    print(f"✅ Tid loggad för hund {hund_id}: {tid:.3f} s")
                    visa_loggningsstatus(loggade_tider, startlista)
                aktiv_hund = None
                klick_före = klick_efter = frame_före = frame_efter = None

    cv2.setMouseCallback("Analys", klick)

    while True:
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa frame.")
            break
        frame = cv2.resize(frame, (fönster_bredd, fönster_höjd), interpolation=cv2.INTER_AREA)
        aktuell_frame = frame.copy()
        tid = frame_tider[frame_index] if frame_tider and frame_index < len(frame_tider) else (frame_index / fps) + fördröjning
        overlay = rita_overlay(aktuell_frame, mållinje_x_scaled, None)
        cv2.putText(overlay, f"Frame: {frame_index}/{total_frames}", (10, 70),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, (200, 200, 200), 2)
        cv2.imshow("Analys", overlay)
        tangent = cv2.waitKey(0) & 0xFF

        if tangent == ord('q'):
            break
        elif tangent == ord('a'):
            frame_index = max(0, frame_index - 1)
        elif tangent == ord('d'):
            frame_index = min(total_frames - 1, frame_index + 1)
        elif tangent in [ord('1'), ord('2'), ord('3'), ord('4'), ord('5'), ord('6')]:
            aktiv_hund = int(chr(tangent))
            print(f"🎯 Loggar hund {aktiv_hund}. Klicka nos före och efter målgång.")
        elif tangent == ord('z'):
            hund_id = input("🗑️ Ange hundnummer att radera tider för: ").strip()
            if hund_id in loggade_tider:
                del loggade_tider[hund_id]
                print(f"↩️ Alla tider för hund {hund_id} borttagna.")
            else:
                print("ℹ️ Ingen tid loggad för den hunden.")

    cv2.destroyWindow("Analys")
    return loggade_tider

def spara_analysresultat(videofil, loggade_tider):
    tidstext = datetime.now().strftime("%H-%M-%S")
    datum_mapp = os.path.dirname(videofil)
    basnamn = os.path.basename(videofil).replace(".avi", "")
    filnamn = f"{sanera_filnamn(basnamn)}__analys__{tidstext}.json"
    sökväg = relativ_sökväg(datum_mapp, filnamn)

    with open(sökväg, "w") as f:
        json.dump(loggade_tider, f, indent=2, ensure_ascii=False)

    print(f"💾 Analysresultat sparat: {sökväg}")
