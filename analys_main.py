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

def hantera_analysval(index, matchande_videor):
    print("\n🎞️ Tillgängliga videor:")
    for i, filnamn in enumerate(matchande_videor, start=1):
        print(f"  {i}. {filnamn}")

    print("\n🧭 Tangenter: [v] välj video, [s] sammanfatta, [r] radera tider, [q] avsluta")
    val = input("👉 Välj: ").strip().lower()

    if val == "v":
        try:
            val_num = int(input(f"👉 Ange videonummer (1–{len(matchande_videor)}): ").strip())
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
        return

    print(f"\n📁 Laddar analys för lopp: {valt_loppnamn}")
    print(f"🎞️ Antal videor att analysera: {len(matchande)}")

    index = 0
    loggade_tider_total = {}

    while True:
        val = hantera_analysval(index, matchande)
        if val == "avsluta":
            break
        elif val == "sammanfatta":
            visa_sammanfattning(valt_loppnamn, loggade_tider_total, startlista_dict)
            continue
        elif val == "radera":
            hund_id = input("🗑️ Ange hundnummer att återställa till DNF: ").strip()
            if hund_id in loggade_tider_total:
                loggade_tider_total[hund_id] = "DNF"
                print(f"↩️ Alla tider för hund {hund_id} återställda till DNF.")
            else:
                print("ℹ️ Ingen tid loggad för den hunden.")
            continue
        elif isinstance(val, int):
            index = val
        else:
            continue  # Ogiltigt val, upprepa

        aktuell_fil = os.path.join(videomapp, matchande[index])
        print(f"\n🎞️ Öppnar video {index+1}/{len(matchande)}: {matchande[index]}")
        cap, metadata, startlista_dict, loppnamn, startlista_namn = ladda_video_och_metadata(aktuell_fil, valt_loppnamn)
        if not cap:
            print("❌ Kunde inte ladda video.")
            return

        loggade_tider = hantera_loggning(cap, metadata, startlista_dict)

        # Slå ihop tider
        for hund, tider in loggade_tider.items():
            if hund not in loggade_tider_total:
                loggade_tider_total[hund] = []
            loggade_tider_total[hund].extend(tider if isinstance(tider, list) else [tider])

    # Avslutande sammanfattning
    print("\n📋 Slutlig sammanfattning:")
    visa_sammanfattning(valt_loppnamn, loggade_tider_total, startlista_dict)

    # Automatisk sparning om tider finns
    if loggade_tider_total:
        from metadata import spara_metadata_och_frame_tider as spara_resultat
        spara_analysresultat(aktuell_fil, loggade_tider_total)

        loppnamn_sanerat = sanera_filnamn(valt_loppnamn)
        spara_sammanfattning_json(startlista_namn, loppnamn_sanerat, loggade_tider_total, metadata, startlista_dict)
        fråga_om_export(startlista_namn, loppnamn_sanerat, loggade_tider_total, startlista_dict)

        print("💾 Resultat sparat automatiskt.")
    else:
        print("⚠️ Inga tider loggade – resultat sparas inte.")

    print("🏁 Analys klar.")

    # Hoppa till nästa lopp om tillåtet
    if tillåt_nästa_lopp and startlista_namn and startlista and lopp_index is not None:
        from tavling import starta_tavlingsläge
        if isinstance(startlista, list):
            if lopp_index + 1 < len(startlista):
                nästa_lopp = startlista[lopp_index + 1]
                print(f"\n⏱️ Nästa lopp: {nästa_lopp['lopp_namn']}")
                config = ladda_config()
                config["senaste_lopp_id"] = lopp_index + 2
                starta_tavlingsläge(config, startlista_namn, startlista, lopp_index + 1, hoppa_fortsättningsfråga=True)
            else:
                print("✅ Alla lopp är analyserade – tävlingspasset är klart.")
        else:
            print("⚠️ Kunde inte hoppa till nästa lopp – startlista saknas eller är inte en lista.")

