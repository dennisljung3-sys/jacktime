# inspelning.py
import cv2
import time
import os
from textutils import ersätt_svenska_tecken
from fönsterhanterare import get_fönster
from fifo_input import läs_tangent_från_kö, skriv_status   # ⭐ NYTT


def rita_overlay(frame, mållinje_x=None, tid_str=None):
    höjd, bredd = frame.shape[:2]
    x = mållinje_x if mållinje_x is not None else bredd // 2
    cv2.line(frame, (x, 0), (x, höjd), (0, 0, 255), 2)
    if tid_str:
        tid_str = ersätt_svenska_tecken(tid_str)
        cv2.putText(
            frame, tid_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2
        )
    return frame


def kör_inspelningsloop(
    cap,
    config,
    start_tid,
    spara_mapp,
    filnamnsbas,
    mållinje_x=None,
    max_tid_för_frame_tider=75,
):
    """
    Kör inspelningsloopen - ANVÄNDER SAMMA CAP SOM FÖNSTERHANTERAREN
    """
    # Hämta fönsterhanteraren
    fönster = get_fönster()
    if fönster is None:
        print("❌ Fönsterhanteraren är inte tillgänglig!")
        return []

    inspelning_aktiv = False
    inspelningar = []
    fps = config["kamera_fps"]
    justerad_latens_ms = config.get("justerad_latens_ms", 0)

    # ⭐ NYTT: Räknare för status-uppdatering
    frame_räknare = 0
    senaste_status_tid = time.time()
    STATUS_INTERVAL_S = 0.2       # 200 ms
    STATUS_INTERVAL_FRAMES = 30   # var 30:e frame

    print("🎬 Tryck [mellanslag] för att starta/pausa inspelning, [q] för att avsluta.")

    # Skriv status direkt vid start
    skriv_status(
        "inspelning_redo",
        meddelande="Tryck Starta inspelning (mellanslag) för att börja",
    )

    # Kontrollera att kameran fungerar
    test_ret, test_frame = cap.read()
    if not test_ret:
        print("❌ Kameran fungerar inte! Kan inte starta inspelning.")
        return []

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        # ⭐ ROTERA BILDEN 90° MOTURS
        frame = cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)

        # Hämta nya dimensioner efter rotation (behövs för REC-indikator)
        höjd, bredd = frame.shape[:2]

        elapsed = time.time() - start_tid
        justerad_tid = elapsed - (justerad_latens_ms / 1000)
        tid_str = f"{justerad_tid:.3f} s"

        # Skapa en kopia för visning
        frame_overlay = frame.copy()

        # Rita mållinje och tid
        frame_overlay = rita_overlay(frame_overlay, mållinje_x, tid_str)

        # Om inspelning pågår, spara till video och visa REC-indikator
        if inspelning_aktiv:
            rec_x = bredd - 100
            rec_y = 30
            cv2.circle(frame_overlay, (rec_x, rec_y), 10, (0, 0, 255), -1)
            cv2.putText(
                frame_overlay,
                "REC",
                (rec_x + 20, rec_y + 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 0, 255),
                2,
            )

            # Starta ny inspelning om ingen aktiv
            if not inspelningar or not inspelningar[-1]["aktiv"]:
                inspelnings_start_tid = time.time()
                inspelningsnummer = len(inspelningar) + 1
                filnamn = f"{filnamnsbas}__{inspelningsnummer}.avi"
                sökväg = os.path.join(spara_mapp, filnamn)
                writer = cv2.VideoWriter(
                    sökväg, cv2.VideoWriter_fourcc(*"XVID"), fps, (bredd, höjd)
                )
                inspelningar.append(
                    {
                        "fil": sökväg,
                        "writer": writer,
                        "aktiv": True,
                        "starttid": inspelnings_start_tid,
                        "frame_tider": [],
                        "inspelningsnummer": inspelningsnummer,
                    }
                )

            # Skriv frame till video
            inspelningar[-1]["writer"].write(frame_overlay)

            # Spara frame-tider (bara för första 75 sekunderna)
            inspelningstid = time.time() - inspelningar[-1]["starttid"]
            if inspelningstid <= max_tid_för_frame_tider:
                inspelningar[-1]["frame_tider"].append(round(justerad_tid, 6))

        # Visa bilden i fönsterhanteraren
        cv2.imshow(fönster.fönster_namn, frame_overlay)

        # ⭐ Läs tangent från videofönstret
        tangent = cv2.waitKey(1) & 0xFF

        # ⭐ NYTT: Läs även från kön (FIFO eller terminal)
        kö_kommando = läs_tangent_från_kö()

        # ⭐ Hantera mellanslag (start/paus) – från video ELLER kö
        mellanslag_tryckt = (tangent == ord(" ")) or (
            kö_kommando is not None and kö_kommando.strip() == ""
        ) or (kö_kommando is not None and kö_kommando.strip() == " ")

        if mellanslag_tryckt:
            inspelning_aktiv = not inspelning_aktiv
            print("▶️ Startar inspelning" if inspelning_aktiv else "⏸️ Pausar inspelning")
            if not inspelning_aktiv and inspelningar:
                inspelningar[-1]["writer"].release()
                inspelningar[-1]["aktiv"] = False

        # ⭐ Hantera q (avsluta) – från video ELLER kö
        q_tryckt = (tangent == ord("q")) or (
            kö_kommando is not None and kö_kommando.strip().lower() == "q"
        )
        if q_tryckt:
            print("🛑 Avslutar inspelning.")
            break

        # ⭐ NYTT: Uppdatera status var 30:e frame eller var 200 ms
        frame_räknare += 1
        nu = time.time()
        if (
            frame_räknare % STATUS_INTERVAL_FRAMES == 0
            or (nu - senaste_status_tid) >= STATUS_INTERVAL_S
        ):
            if inspelning_aktiv:
                skriv_status(
                    "inspelning_pagar",
                    tid=round(justerad_tid, 2),
                    aktiv=True,
                    antal_inspelningar=len(inspelningar),
                    meddelande=f"Spelar in... {justerad_tid:.1f} s",
                )
            else:
                skriv_status(
                    "inspelning_pausad",
                    tid=round(justerad_tid, 2),
                    aktiv=False,
                    meddelande="Inspelning pausad",
                )
            senaste_status_tid = nu

    # Stoppa eventuell pågående inspelning
    for insp in inspelningar:
        if insp["aktiv"]:
            insp["writer"].release()

    # ⭐ NYTT: Slutlig status
    skriv_status(
        "inspelning_avslutad",
        antal_inspelningar=len(inspelningar),
        meddelande=f"Inspelning klar – {len(inspelningar)} fil(er) sparade",
    )

    return inspelningar
