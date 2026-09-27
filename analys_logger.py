# analys_logger.py - Komplett version med adaptiv storlek och bevarad aspect ratio
import cv2
import os
import json
import numpy as np
from datetime import datetime
from paths import relativ_sökväg
from textutils import sanera_filnamn
from fönsterhanterare import get_fönster
from fifo_input import läs_tangent_från_kö, skriv_status   # ⭐ NYTT


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
    # Hämta fönsterhanteraren
    fönster = get_fönster()
    if fönster is None:
        print("❌ Fönsterhanteraren är inte tillgänglig!")
        return {}

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

    # Original dimensioner (videon är redan roterad från inspelningen)
    ursprunglig_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    ursprunglig_höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # ⭐ HÄMTA SKÄRMUPPLÖSNING
    try:
        import tkinter as tk

        root = tk.Tk()
        root.withdraw()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()
    except:
        screen_width = 1920
        screen_height = 1080

    # ⭐ BERÄKNA MAXIMAL STORLEK (halva skärmen med marginal)
    max_bredd = screen_width // 2 - 50
    max_höjd = screen_height - 100

    print(f"🖥️ Skärmupplösning: {screen_width}x{screen_height}")
    print(f"📐 Maximal fönsterstorlek: {max_bredd}x{max_höjd}")

    # ⭐ BERÄKNA OPTIMAL STORLEK (behåll aspect ratio)
    skal_x = max_bredd / ursprunglig_bredd
    skal_y = max_höjd / ursprunglig_höjd
    skal = min(skal_x, skal_y)

    fönster_bredd = int(ursprunglig_bredd * skal)
    fönster_höjd = int(ursprunglig_höjd * skal)

    print(f"📐 Videons originalstorlek: {ursprunglig_bredd}x{ursprunglig_höjd}")
    print(
        f"📐 Visningsstorlek (bevarad aspect ratio): {fönster_bredd}x{fönster_höjd} (skal: {skal:.2f}x)"
    )

    # Spara gamla inställningar för att kunna återställa senare
    gammal_bredd = fönster.bredd
    gammal_höjd = fönster.höjd
    gammal_x = fönster.x_pos
    gammal_y = fönster.y_pos

    # Uppdatera fönsterstorleken
    fönster.bredd = fönster_bredd
    fönster.höjd = fönster_höjd

    # ⭐ Placera fönstret på höger halva av skärmen, centrerat vertikalt
    fönster.x_pos = screen_width // 2 + (max_bredd - fönster_bredd) // 2
    fönster.y_pos = (screen_height - fönster_höjd) // 2

    cv2.resizeWindow(fönster.fönster_namn, fönster_bredd, fönster_höjd)
    cv2.moveWindow(fönster.fönster_namn, fönster.x_pos, fönster.y_pos)

    visad_bredd = fönster_bredd
    visad_höjd = fönster_höjd
    offset_x = 0
    offset_y = 0

    mållinje_x = metadata.get("mållinje_x")
    mållinje_x_scaled = int(mållinje_x * skal) if mållinje_x else None

    loggade_tider = {str(nr): "DNF" for nr in startlista.keys()}
    frame_index = 0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    aktiv_hund = None
    klick_före = klick_efter = frame_före = frame_efter = None

    # Spara data i fönsterhanterarens läges_data så att callback kan komma åt den
    fönster.läges_data.update(
        {
            "analys_cap": cap,
            "analys_metadata": metadata,
            "analys_frame_index": frame_index,
            "analys_total_frames": total_frames,
            "analys_aktiv_hund": None,
            "analys_klick_före": None,
            "analys_klick_efter": None,
            "analys_frame_före": None,
            "analys_frame_efter": None,
            "analys_skal": skal,
            "analys_offset_x": offset_x,
            "analys_offset_y": offset_y,
            "analys_visad_bredd": visad_bredd,
            "analys_visad_höjd": visad_höjd,
            "analys_mållinje_x": mållinje_x,
            "analys_mållinje_x_scaled": mållinje_x_scaled,
            "analys_fps": fps,
            "analys_fördröjning": fördröjning,
            "analys_frame_tider": frame_tider,
            "analys_loggade_tider": loggade_tider,
            "analys_startlista": startlista,
            "analys_ursprunglig_bredd": ursprunglig_bredd,
            "analys_ursprunglig_höjd": ursprunglig_höjd,
            "analys_gammal_bredd": gammal_bredd,
            "analys_gammal_höjd": gammal_höjd,
            "analys_gammal_x": gammal_x,
            "analys_gammal_y": gammal_y,
        }
    )

    def mus_klick(event, x, y, flags, param):
        """Hanterar musklick för analys - anropas från fönsterhanteraren"""
        if event == cv2.EVENT_LBUTTONDOWN:
            aktiv = fönster.läges_data.get("analys_aktiv_hund")
            if aktiv is None:
                return

            skal = fönster.läges_data["analys_skal"]
            ursprunglig_x = int(x / skal)

            klick_före_val = fönster.läges_data.get("analys_klick_före")
            klick_efter_val = fönster.läges_data.get("analys_klick_efter")
            frame_idx = fönster.läges_data.get("analys_frame_index", 0)

            if klick_före_val is None:
                # Första klicket - före målgång
                fönster.läges_data["analys_klick_före"] = ursprunglig_x
                fönster.läges_data["analys_frame_före"] = frame_idx
                print(
                    f"🐾 Hund {aktiv}: nos före målgång markerad (frame {frame_idx}, x={ursprunglig_x})"
                )
                # ⭐ NYTT: Status till GUI:t
                skriv_status(
                    "analys_markerar",
                    hund=aktiv,
                    steg="före",
                    frame=frame_idx,
                    x=ursprunglig_x,
                    meddelande=f"Hund {aktiv}: Klicka nos EFTER mållinjen",
                )
            elif klick_efter_val is None:
                # Andra klicket - efter målgång
                fönster.läges_data["analys_klick_efter"] = ursprunglig_x
                fönster.läges_data["analys_frame_efter"] = frame_idx
                print(
                    f"🐾 Hund {aktiv}: nos efter målgång markerad (frame {frame_idx}, x={ursprunglig_x})"
                )

                # Beräkna tid
                frame_före_val = fönster.läges_data["analys_frame_före"]
                frame_efter_val = frame_idx
                klick_före_x = fönster.läges_data["analys_klick_före"]
                klick_efter_x = ursprunglig_x
                frame_tider_lista = fönster.läges_data.get("analys_frame_tider")
                fps_val = fönster.läges_data["analys_fps"]
                fördröjning_val = fönster.läges_data["analys_fördröjning"]
                mållinje_x_val = fönster.läges_data["analys_mållinje_x"]

                if (
                    frame_tider_lista
                    and frame_före_val < len(frame_tider_lista)
                    and frame_efter_val < len(frame_tider_lista)
                ):
                    tid_före = frame_tider_lista[frame_före_val]
                    tid_efter = frame_tider_lista[frame_efter_val]
                else:
                    tid_före = frame_före_val / fps_val + fördröjning_val
                    tid_efter = frame_efter_val / fps_val + fördröjning_val

                tid = logga_tid(
                    aktiv,
                    tid_före,
                    tid_efter,
                    klick_före_x,
                    klick_efter_x,
                    mållinje_x_val,
                )
                if tid is not None:
                    hund_id = str(aktiv)
                    loggade = fönster.läges_data.get("analys_loggade_tider", {})
                    loggade[hund_id] = [tid]
                    fönster.läges_data["analys_loggade_tider"] = loggade
                    print(f"✅ Tid loggad för hund {hund_id}: {tid:.3f} s")
                    visa_loggningsstatus(
                        loggade, fönster.läges_data["analys_startlista"]
                    )
                    # ⭐ NYTT: Status till GUI:t
                    skriv_status(
                        "analys_tid_loggad",
                        hund=aktiv,
                        tid=tid,
                        loggade_tider=loggade,
                        meddelande=f"Hund {aktiv}: {tid:.3f} s – välj nästa hund",
                    )

                # Återställ för nästa hund
                fönster.läges_data["analys_aktiv_hund"] = None
                fönster.läges_data["analys_klick_före"] = None
                fönster.läges_data["analys_klick_efter"] = None
                fönster.läges_data["analys_frame_före"] = None
                fönster.läges_data["analys_frame_efter"] = None

    def tangent_callback(tangent):
        """Hanterar tangentbord för analys"""
        if tangent == ord("q"):
            fönster.läges_data["analys_avsluta"] = True
        elif tangent == ord("a"):
            ny_frame = max(0, fönster.läges_data.get("analys_frame_index", 0) - 1)
            fönster.läges_data["analys_frame_index"] = ny_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, ny_frame)
        elif tangent == ord("d"):
            ny_frame = min(
                fönster.läges_data.get("analys_total_frames", 0) - 1,
                fönster.läges_data.get("analys_frame_index", 0) + 1,
            )
            fönster.läges_data["analys_frame_index"] = ny_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, ny_frame)
        elif tangent in [ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")]:
            hund = int(chr(tangent))
            fönster.läges_data["analys_aktiv_hund"] = hund
            fönster.läges_data["analys_klick_före"] = None
            fönster.läges_data["analys_klick_efter"] = None
            print(f"🎯 Loggar hund {hund}. Klicka nos före och efter målgång.")

    # Sätt callbacks i fönsterhanteraren
    fönster.läges_data["analys_avsluta"] = False
    fönster.läges_data["mus_callback"] = mus_klick
    fönster.läges_data["tangent_callback"] = tangent_callback

    # Byt läge till analys
    fönster.byt_läge("analys")

    # Sätt mus-callback
    cv2.setMouseCallback(fönster.fönster_namn, mus_klick)

    # ⭐ NYTT: Skriv status till GUI:t när analysen börjar
    skriv_status(
        "analys_redo",
        hundar={
            nr: info.get("namn", f"Hund {nr}")
            for nr, info in startlista.items()
        },
        loggade_tider=loggade_tider,
        total_frames=total_frames,
        frame=0,
        meddelande="Välj hund (1-6) för att börja logga, eller A/D för att navigera",
    )

    # ⭐ Räknare för status-uppdatering
    frame_räknare = 0
    senaste_status_tid = datetime.now().timestamp()
    STATUS_INTERVAL_S = 0.2
    STATUS_INTERVAL_FRAMES = 30

    # Huvudloop för analys
    while not fönster.läges_data.get("analys_avsluta", False):
        cap.set(cv2.CAP_PROP_POS_FRAMES, fönster.läges_data["analys_frame_index"])
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa frame.")
            break

        frame = cv2.resize(
            frame, (fönster_bredd, fönster_höjd), interpolation=cv2.INTER_AREA
        )

        frame_idx = fönster.läges_data["analys_frame_index"]
        tid = (
            frame_tider[frame_idx]
            if frame_tider and frame_idx < len(frame_tider)
            else (frame_idx / fps) + fördröjning
        )

        overlay = frame.copy()

        if mållinje_x_scaled is not None and 0 <= mållinje_x_scaled < fönster_bredd:
            cv2.line(
                overlay,
                (mållinje_x_scaled, 0),
                (mållinje_x_scaled, fönster_höjd),
                (0, 0, 255),
                2,
            )

        if tid:
            cv2.putText(
                overlay,
                f"Tid: {tid:.3f} s",
                (10, 40),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

        cv2.putText(
            overlay,
            f"Frame: {frame_idx}/{total_frames}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2,
        )

        aktiv = fönster.läges_data.get("analys_aktiv_hund")
        if aktiv is not None:
            cv2.putText(
                overlay,
                f"Aktiv hund: {aktiv}",
                (10, 100),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 255),
                2,
            )

        cv2.putText(
            overlay,
            "A/D = BACKA/FRAM, 1-6 = VAL AV HUND, Q = AVSLUTA",
            (10, fönster_höjd - 20),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 0, 255),
            2,
        )

        cv2.imshow(fönster.fönster_namn, overlay)

        # ⭐ Läs tangent från videofönstret
        tangent = cv2.waitKey(1) & 0xFF

        # ⭐ NYTT: Läs även från kön
        kö_kommando = läs_tangent_från_kö()

        # ⭐ Hantera tangent från video
        if tangent != 255:
            tangent_callback(tangent)

        # ⭐ NYTT: Hantera kommando från kön
        if kö_kommando is not None:
            kommando_lower = kö_kommando.strip().lower()
            # Mappa kö-kommandon till "tangent"-koder
            if kommando_lower == "q":
                tangent_callback(ord("q"))
            elif kommando_lower == "a":
                tangent_callback(ord("a"))
            elif kommando_lower == "d":
                tangent_callback(ord("d"))
            elif kommando_lower in ["1", "2", "3", "4", "5", "6"]:
                tangent_callback(ord(kommando_lower))
            elif kommando_lower == "":
                # Enter – ignorera i analysläget (används inte)
                pass
            else:
                print(f"ℹ️ Ignorerar kommando i analys: '{kö_kommando}'")

        # ⭐ NYTT: Uppdatera status var 30:e frame eller var 200 ms
        frame_räknare += 1
        nu = datetime.now().timestamp()
        if (
            frame_räknare % STATUS_INTERVAL_FRAMES == 0
            or (nu - senaste_status_tid) >= STATUS_INTERVAL_S
        ):
            skriv_status(
                "analys_pagar",
                frame=frame_idx,
                total_frames=total_frames,
                tid=round(tid, 3) if tid else None,
                aktiv_hund=fönster.läges_data.get("analys_aktiv_hund"),
                loggade_tider=fönster.läges_data.get("analys_loggade_tider", {}),
                meddelande=f"Frame {frame_idx}/{total_frames}",
            )
            senaste_status_tid = nu

    # ⭐ Återställ fönsterstorleken till ursprunglig
    cv2.resizeWindow(fönster.fönster_namn, gammal_bredd, gammal_höjd)
    cv2.moveWindow(fönster.fönster_namn, gammal_x, gammal_y)
    fönster.bredd = gammal_bredd
    fönster.höjd = gammal_höjd
    fönster.x_pos = gammal_x
    fönster.y_pos = gammal_y

    # Rensa callbacks
    fönster.läges_data.pop("mus_callback", None)
    fönster.läges_data.pop("tangent_callback", None)
    fönster.byt_läge("tom")

    return fönster.läges_data.get("analys_loggade_tider", {})


def spara_analysresultat(videofil, loggade_tider):
    tidstext = datetime.now().strftime("%H-%M-%S")
    datum_mapp = os.path.dirname(videofil)
    basnamn = os.path.basename(videofil).replace(".avi", "")
    filnamn = f"{sanera_filnamn(basnamn)}__analys__{tidstext}.json"
    sökväg = relativ_sökväg(datum_mapp, filnamn)

    with open(sökväg, "w") as f:
        json.dump(loggade_tider, f, indent=2, ensure_ascii=False)

    print(f"💾 Analysresultat sparat: {sökväg}")
