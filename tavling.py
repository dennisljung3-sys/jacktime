import os
import datetime
from tidtagning_core import förbered_kamera_och_mållinje
from startsensor import vänta_på_startsignal
from inspelning import kör_inspelningsloop
from metadata import spara_metadata_och_frame_tider
from analys_main import starta_analysläge
from gemensamt import ladda_startlista
from textutils import sanera_filnamn

def välj_startlista():
    filer = [f for f in os.listdir("startlistor") if f.endswith(".json")]
    if not filer:
        print("❌ Inga startlistor hittades.")
        return None
    print("\n📁 Tillgängliga startlistor:")
    for i, fil in enumerate(filer, 1):
        print(f"{i}. {fil}")
    val = input("👉 Välj startlista (nummer): ").strip()
    if not val.isdigit() or not (1 <= int(val) <= len(filer)):
        print("❌ Ogiltigt val.")
        return None
    return os.path.splitext(filer[int(val) - 1])[0]

def välj_lopp(startlista):
    print("\n🏁 Tillgängliga lopp:")
    for i, lopp in enumerate(startlista, 1):
        print(f"{i}. {lopp['lopp_namn']} ({len(lopp['hundar'])} hundar)")
    val = input("👉 Välj lopp (nummer): ").strip()
    if not val.isdigit() or not (1 <= int(val) <= len(startlista)):
        print("❌ Ogiltigt val.")
        return None, None
    index = int(val) - 1
    return startlista[index], index

def starta_tavlingsläge(config, startlista_namn=None, startlista=None, lopp_index=None, hoppa_fortsättningsfråga=False):
    print("\n🏁 Startar tävlingsläge...")

    if not startlista_namn:
        startlista_namn = välj_startlista()
        if not startlista_namn:
            return

    if not startlista:
        startlista = ladda_startlista(startlista_namn)
        if not startlista:
            print("❌ Startlistan är tom eller ogiltig.")
            return

    if lopp_index is None:
        valt_lopp, lopp_index = välj_lopp(startlista)
        if not valt_lopp:
            return
    else:
        valt_lopp = startlista[lopp_index]

    spara_mapp = os.path.join("resultat", sanera_filnamn(startlista_namn))
    if os.path.isfile(spara_mapp):
        print(f"⚠️ En fil med namnet '{spara_mapp}' blockerar sparning. Ta bort den först.")
        return
    os.makedirs(spara_mapp, exist_ok=True)

    cap, metadata = förbered_kamera_och_mållinje(config)
    config["mållinje_x"] = metadata.get("mållinje_x")
    config["skärmstorlek"] = metadata.get("skärmstorlek")

    input("\n⏳ Tryck [enter] när du är redo att ta emot startsignal...")
    start_tid = vänta_på_startsignal(config["arduino_port"])
    if start_tid is None:
        print("↩️ Tidtagning avbruten – återgår till huvudmenyn.")
        return

    tidtagning_str = datetime.datetime.fromtimestamp(start_tid).strftime("%H-%M-%S")
    loppnamn_rensad = sanera_filnamn(valt_lopp["lopp_namn"])
    filnamnsbas = f"Lopp-{lopp_index+1}__{loppnamn_rensad}__{tidtagning_str}"
    inspelningar = kör_inspelningsloop(cap, config, start_tid, spara_mapp, filnamnsbas, config["mållinje_x"])

    for insp in inspelningar:
        insp["lopp_index"] = lopp_index + 1
        insp["lopp_namn"] = valt_lopp["lopp_namn"]
        spara_metadata_och_frame_tider(insp, config, start_tid)

    svar = input("\n🔍 Vill du analysera det här loppet direkt? (j/n): ").strip().lower()
    if svar == "j":
        senaste_video = inspelningar[-1]["fil"]
        starta_analysläge(
            videofil=senaste_video,
            valt_loppnamn=valt_lopp["lopp_namn"],
            tillåt_nästa_lopp=True,
            startlista_namn=startlista_namn,
            startlista=startlista,
            lopp_index=lopp_index
        )

    if not hoppa_fortsättningsfråga:
        svar2 = input("\n⏭️ Vill du ta tid i nästa lopp? (j/n): ").strip().lower()
        if svar2 == "j" and lopp_index + 1 < len(startlista):
            config["senaste_lopp_id"] = lopp_index + 2
            nästa_lopp = startlista[lopp_index + 1]
            print(f"\n⏱️ Nästa lopp: {nästa_lopp['lopp_namn']}")
            starta_tavlingsläge(config, startlista_namn, startlista, lopp_index + 1)
        else:
            print("🏁 Tävlingspass avslutat.")

