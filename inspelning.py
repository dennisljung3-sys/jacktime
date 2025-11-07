import cv2
import time
import os
from textutils import ersätt_svenska_tecken

def rita_overlay(frame, mållinje_x=None, tid_str=None):
    höjd, bredd = frame.shape[:2]
    x = mållinje_x if mållinje_x is not None else bredd // 2
    cv2.line(frame, (x, 0), (x, höjd), (0, 0, 255), 2)
    if tid_str:
        tid_str = ersätt_svenska_tecken(tid_str)
        cv2.putText(frame, tid_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    return frame

def kör_inspelningsloop(cap, config, start_tid, spara_mapp, filnamnsbas, mållinje_x=None, max_tid_för_frame_tider=75):
    screen_width = config.get("skärmstorlek", [1280, 720])[0]
    fönster_bredd = screen_width // 2
    fönster_höjd = fönster_bredd * 9 // 16
    x_pos = screen_width // 2
    y_pos = 0

    inspelning_aktiv = False
    inspelningar = []
    fps = config["kamera_fps"]
    justerad_latens_ms = config.get("justerad_latens_ms", 0)

    print("🎬 Tryck [mellanslag] för att starta/pausa inspelning, [q] för att avsluta.")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        elapsed = time.time() - start_tid
        justerad_tid = elapsed - (justerad_latens_ms / 1000)
        tid_str = f"{justerad_tid:.3f} s"
        frame_overlay = rita_overlay(frame.copy(), mållinje_x, tid_str)

        if inspelning_aktiv:
            höjd, bredd = frame_overlay.shape[:2]
            rec_x = bredd - 100
            rec_y = 30
            cv2.circle(frame_overlay, (rec_x, rec_y), 10, (0, 0, 255), -1)
            cv2.putText(frame_overlay, "REC", (rec_x + 20, rec_y + 8), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

            if not inspelningar or not inspelningar[-1]["aktiv"]:
                inspelnings_start_tid = time.time()
                inspelningsnummer = len(inspelningar) + 1
                filnamn = f"{filnamnsbas}__{inspelningsnummer}.avi"
                sökväg = os.path.join(spara_mapp, filnamn)
                writer = cv2.VideoWriter(sökväg, cv2.VideoWriter_fourcc(*'XVID'), fps, (bredd, höjd))
                inspelningar.append({
                    "fil": sökväg,
                    "writer": writer,
                    "aktiv": True,
                    "starttid": inspelnings_start_tid,
                    "frame_tider": [],
                    "inspelningsnummer": inspelningsnummer
                })
            inspelningar[-1]["writer"].write(frame_overlay)

            inspelningstid = time.time() - inspelningar[-1]["starttid"]
            if inspelningstid <= max_tid_för_frame_tider:
                inspelningar[-1]["frame_tider"].append(round(justerad_tid, 6))

        cv2.namedWindow("Tidtagning", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("Tidtagning", fönster_bredd, fönster_höjd)
        cv2.moveWindow("Tidtagning", x_pos, y_pos)
        cv2.imshow("Tidtagning", frame_overlay)
        tangent = cv2.waitKey(1) & 0xFF
        if tangent == ord(' '):
            inspelning_aktiv = not inspelning_aktiv
            print("▶️ Startar inspelning" if inspelning_aktiv else "⏸️ Pausar inspelning")
            if not inspelning_aktiv and inspelningar:
                inspelningar[-1]["writer"].release()
                inspelningar[-1]["aktiv"] = False
        elif tangent == ord('q'):
            print("🛑 Avslutar inspelning.")
            break

    cap.release()
    for insp in inspelningar:
        if insp["aktiv"]:
            insp["writer"].release()
    cv2.destroyAllWindows()
    return inspelningar
