# analys_main.py - FIXAD VERSION med kamerafrigöring
from paths import relativ_sökväg
import os
import cv2
import json
from analys_loader import ladda_video_och_metadata
from analys_logger import hantera_loggning, spara_analysresultat
from analys_summary import visa_sammanfattning
from textutils import normalisera, sanera_filnamn
from sammanfattning import (
    spara_sammanfattning_json,
    fråga_om_export
)
from confighantering import ladda_config
from fönsterhanterare import get_fönster
from fifo_input import input_från_fifo, skriv_status   # ⭐ NYTT


def hantera_analysval(index, matchande_videor):
    print("\n🎞️ Tillgängliga videor:")
    for i, filnamn in enumerate(matchande_videor, start=1):
        print(f"  {i}. {filnamn}")

    print("\n🧭 Tangenter: [v] välj video, [s] sammanfatta, [r] radera tider, [q] avsluta")

    # ⭐ NYTT: Skriv status till GUI:t
    skriv_status(
        "analys_valj_video",
        videor=[
            {"nr": i, "filnamn": f} for i, f in enumerate(matchande_videor, 1)
        ],
        aktuell_index=index,
        meddelande="Välj video (v), sammanfatta (s), radera (r), avsluta (q)",
    )

    val = input_från_fifo("👉 Välj: ").strip().lower()

    if val == "v":
        # ⭐ NYTT: Status innan vi frågar efter videonummer
        skriv_status(
            "analys_valj_videonummer",
            antal=len(matchande_videor),
            meddelande=f"Ange videonummer (1–{len(matchande_videor)})",
        )
        try:
            val_num_str = input_från_fifo(
                f"👉 Ange videonummer (1–{len(matchande_videor)}): "
            ).strip()
            val_num = int(val_num_str)
            if 1 <= val_num <= len(matchande_videor):
                return val_num - 1
            else:
                print("❌ Ogiltigt nummer.")
                return "upprepa"
        except ValueError:
            print("❌ Ange ett heltal.")
            return "upprepa"
    elif val == "s":
        return "sammanfatta"
    elif val == "r":
        return "radera"
    elif val == "q":
        return "avsluta"
    else:
        print("❌ Ogiltigt val – försök igen.")
        return "upprepa"


def starta_analysläge(videofil, valt_loppnamn=None, tillåt_nästa_lopp=False, startlista_namn=None, startlista=None, lopp_index=None):
    videomapp = os.path.dirname(videofil)
    alla_filer = sorted(f for f in os.listdir(videomapp) if f.endswith(".avi"))
    basnamn = os.path.basename(videofil).replace(".avi", "")

    # Hitta alla videor från samma lopp (baserat på filnamnsstruktur)
    prefix = "__".join(basnamn.split("__")[:2])
    matchande = [f for f in alla_filer if f.startswith(prefix)]
    if not matchande:
        print("❌ Inga matchande videor hittades.")
        skriv_status("fel", meddelande="Inga matchande videor hittades")
        return

    print(f"\n📁 Laddar analys för lopp: {valt_loppnamn}")
    print(f"🎞️ Antal videor att analysera: {len(matchande)}")

    # ⭐ NYTT: Status när analysen startar
    skriv_status(
        "analys_startar",
        lopp=valt_loppnamn,
        antal_videor=len(matchande),
        meddelande=f"Analyserar {valt_loppnamn}",
    )

    index = 0
    loggade_tider_total = {}
    startlista_dict = {}
    aktuell_fil = None
    metadata = {}

    while True:
        val = hantera_analysval(index, matchande)
        if val == "avsluta":
            break
        elif val == "sammanfatta":
            # ⭐ NYTT: Status när sammanfattning visas
            skriv_status(
                "analys_sammanfattning",
                lopp=valt_loppnamn,
                meddelande="Visar sammanfattning",
            )
            visa_sammanfattning(valt_loppnamn, loggade_tider_total, startlista_dict)
            continue
        elif val == "radera":
            # ⭐ NYTT: Status innan vi frågar efter hundnummer
            skriv_status(
                "analys_radera_hund",
                meddelande="Ange hundnummer att återställa till DNF",
            )
            hund_id = input_från_fifo(
                "🗑️ Ange hundnummer att återställa till DNF: "
            ).strip()
            if hund_id in loggade_tider_total:
                loggade_tider_total[hund_id] = "DNF"
                print(f"↩️ Alla tider för hund {hund_id} återställda till DNF.")
            else:
                print("ℹ️ Ingen tid loggad för den hunden.")
            continue
        elif isinstance(val, int):
            index = val
        else:
            continue

        aktuell_fil = os.path.join(videomapp, matchande[index])
        print(f"\n🎞️ Öppnar video {index+1}/{len(matchande)}: {matchande[index]}")

        # ⭐ NYTT: Status när video öppnas
        skriv_status(
            "analys_oppnar_video",
            video_nr=index + 1,
            antal=len(matchande),
            filnamn=matchande[index],
            meddelande=f"Öppnar video {index+1}/{len(matchande)}",
        )

        cap, metadata, startlista_dict, loppnamn, startlista_namn = ladda_video_och_metadata(aktuell_fil, valt_loppnamn)
        if not cap:
            print("❌ Kunde inte ladda video.")
            skriv_status("huvudmeny")
            return

        loggade_tider = hantera_loggning(cap, metadata, startlista_dict)

        # Slå ihop tider
        for hund, tider in loggade_tider.items():
            if hund not in loggade_tider_total:
                loggade_tider_total[hund] = []
            loggade_tider_total[hund].extend(tider if isinstance(tider, list) else [tider])

    # ⭐ FIX: Kolla att vi faktiskt har något att sammanfatta
    if aktuell_fil is None:
        print("ℹ️ Ingen video öppnades – inget att sammanfatta.")
        skriv_status("huvudmeny")
        return

    # Avslutande sammanfattning
    print("\n📋 Slutlig sammanfattning:")
    visa_sammanfattning(valt_loppnamn, loggade_tider_total, startlista_dict)

    # ⭐ FIX: Spara resultat korrekt baserat på typ
    if loggade_tider_total:
        spara_analysresultat(aktuell_fil, loggade_tider_total)

        if valt_loppnamn is None:
            # Träningsläge
            datum = os.path.basename(os.path.dirname(aktuell_fil))
            video_filnamn = os.path.splitext(os.path.basename(aktuell_fil))[0]
            loppnamn_sanerat = sanera_filnamn(video_filnamn)

            mapp = relativ_sökväg("träning", datum)
            os.makedirs(mapp, exist_ok=True)
            filnamn = os.path.join(mapp, f"{loppnamn_sanerat}.json")

            data = {
                "tider": loggade_tider_total,
                "metadata": metadata,
                "startlista": startlista_dict,
                "lopp_namn": video_filnamn,
                "video_fil": os.path.basename(aktuell_fil)
            }

            with open(filnamn, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            print(f"💾 Träningsresultat sparat: {filnamn}")
            fråga_om_export("träning", loppnamn_sanerat, loggade_tider_total, startlista_dict)
        else:
            # Tävlingsläge
            loppnamn_sanerat = sanera_filnamn(valt_loppnamn)
            spara_sammanfattning_json(
                startlista_namn,
                loppnamn_sanerat,
                loggade_tider_total,
                metadata,
                startlista_dict
            )
            fråga_om_export(startlista_namn, loppnamn_sanerat, loggade_tider_total, startlista_dict)

        print("💾 Resultat sparat automatiskt.")
    else:
        print("⚠️ Inga tider loggade – resultat sparas inte.")

    print("🏁 Analys klar.")

    # ⭐ FIX: Frigör kameran INNAN vi går vidare till nästa lopp
    fönster = get_fönster()
    if fönster and fönster.cap is not None:
        fönster.koppla_från_kamera()
        print("📷 Kamera frigjord efter analys.")

    # ⭐ NYTT: Status när analysen är klar
    skriv_status(
        "analys_klar",
        lopp=valt_loppnamn,
        meddelande="Analys klar",
    )

    # Hoppa till nästa lopp om tillåtet
    if tillåt_nästa_lopp and startlista_namn and startlista and lopp_index is not None:
        from tavling import starta_tavlingsläge
        if isinstance(startlista, list):
            if lopp_index + 1 < len(startlista):
                nästa_lopp = startlista[lopp_index + 1]
                print(f"\n⏱️ Nästa lopp: {nästa_lopp['lopp_namn']}")

                # ⭐ NYTT: Status innan nästa lopp
                skriv_status(
                    "analys_nasta_lopp",
                    nästa_lopp=nästa_lopp["lopp_namn"],
                    meddelande=f"Nästa lopp: {nästa_lopp['lopp_namn']}",
                )

                config = ladda_config()
                config["senaste_lopp_id"] = lopp_index + 2

                # ⭐ Liten paus så att kameran hinner frigöras helt
                import time
                time.sleep(0.5)

                starta_tavlingsläge(config, startlista_namn, startlista, lopp_index + 1, hoppa_fortsättningsfråga=True)
            else:
                print("✅ Alla lopp är analyserade – tävlingspasset är klart.")
                skriv_status("huvudmeny")
        else:
            print("⚠️ Kunde inte hoppa till nästa lopp – startlista saknas eller är inte en lista.")
            skriv_status("huvudmeny")
    else:
        # ⭐ NYTT: Tillbaka till huvudmenyn
        skriv_status("huvudmeny")
