# analys_logger.py
import cv2
import os
import json
from datetime import datetime
from analys_overlay import rita_overlay
from paths import relativ_sökväg
from textutils import sanera_filnamn
from fönsterhanterare import get_fönster


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
    ursprunglig_bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    fönster_bredd = fönster.bredd
    skal_x = ursprunglig_bredd / fönster_bredd
    mållinje_x = metadata.get("mållinje_x")
    mållinje_x_scaled = int(mållinje_x / skal_x) if mållinje_x else None

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
            "analys_skal_x": skal_x,
            "analys_mållinje_x": mållinje_x,
            "analys_mållinje_x_scaled": mållinje_x_scaled,
            "analys_fps": fps,
            "analys_fördröjning": fördröjning,
            "analys_frame_tider": frame_tider,
            "analys_loggade_tider": loggade_tider,
            "analys_startlista": startlista,
        }
    )

    def mus_klick(event, x, y, flags, param):
        """Hanterar musklick för analys - anropas från fönsterhanteraren"""
        if event == cv2.EVENT_LBUTTONDOWN:
            # Hämta aktuella värden från fönsterhanteraren
            aktiv = fönster.läges_data.get("analys_aktiv_hund")
            if aktiv is None:
                return

            ursprunglig_x = int(x * fönster.läges_data["analys_skal_x"])
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
            # Backa en frame
            ny_frame = max(0, fönster.läges_data.get("analys_frame_index", 0) - 1)
            fönster.läges_data["analys_frame_index"] = ny_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, ny_frame)
        elif tangent == ord("d"):
            # Fram en frame
            ny_frame = min(
                fönster.läges_data.get("analys_total_frames", 0) - 1,
                fönster.läges_data.get("analys_frame_index", 0) + 1,
            )
            fönster.läges_data["analys_frame_index"] = ny_frame
            cap.set(cv2.CAP_PROP_POS_FRAMES, ny_frame)
        elif tangent in [ord("1"), ord("2"), ord("3"), ord("4"), ord("5"), ord("6")]:
            # Välj hund
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

    # Huvudloop för analys
    while not fönster.läges_data.get("analys_avsluta", False):
        # Hämta frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, fönster.läges_data["analys_frame_index"])
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa frame.")
            break

        # Skala om till fönsterstorlek
        frame = cv2.resize(
            frame, (fönster.bredd, fönster.höjd), interpolation=cv2.INTER_AREA
        )

        # Beräkna tid
        frame_idx = fönster.läges_data["analys_frame_index"]
        tid = (
            frame_tider[frame_idx]
            if frame_tider and frame_idx < len(frame_tider)
            else (frame_idx / fps) + fördröjning
        )

        # Rita overlay
        overlay = rita_overlay(frame, mållinje_x_scaled, None)
        cv2.putText(
            overlay,
            f"Frame: {frame_idx}/{total_frames}",
            (10, 70),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2,
        )

        # Visa aktiv hund om vald
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

        # Visa i fönsterhanteraren
        cv2.imshow(fönster.fönster_namn, overlay)

        # Hantera tangentbord
        tangent = cv2.waitKey(1) & 0xFF

        # Anropa tangent_callback om tangent tryckts
        if tangent != 255:  # 255 betyder ingen tangent
            tangent_callback(tangent)

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
