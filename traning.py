from paths import relativ_sökväg
import os
import datetime
from tidtagning_core import förbered_kamera_och_mållinje
from startsensor import vänta_på_startsignal
from inspelning import kör_inspelningsloop
from metadata import spara_metadata_och_frame_tider
from analys_main import starta_analysläge
from textutils import sanera_filnamn

def skapa_traningsmapp():
    basmapp = relativ_sökväg("träning")
    os.makedirs(basmapp, exist_ok=True)
    datum = datetime.date.today().isoformat()
    dagens_mapp = os.path.join(basmapp, datum)
    if os.path.isfile(dagens_mapp):
        print(f"⚠️ En fil med namnet '{dagens_mapp}' blockerar sparning. Ta bort den först.")
        return None
    os.makedirs(dagens_mapp, exist_ok=True)
    return dagens_mapp

def starta_traningsläge(config):
    print("\n🏋️‍♂️ Startar träningsläge...")
    spara_mapp = skapa_traningsmapp()
    if not spara_mapp:
        return

    cap, metadata = förbered_kamera_och_mållinje(config)
    config["mållinje_x"] = metadata.get("mållinje_x")
    config["skärmstorlek"] = metadata.get("skärmstorlek")

    input("\n⏳ Tryck [enter] när du är redo att ta emot startsignal...")
    start_tid = vänta_på_startsignal(config["arduino_port"])
    if start_tid is None:
        print("↩️ Tidtagning avbruten – återgår till huvudmenyn.")
        return

    tidtagning_str = datetime.datetime.fromtimestamp(start_tid).strftime("%H-%M-%S")
    filnamnsbas = sanera_filnamn(tidtagning_str)
    inspelningar = kör_inspelningsloop(cap, config, start_tid, spara_mapp, filnamnsbas, config["mållinje_x"])

    for insp in inspelningar:
        spara_metadata_och_frame_tider(insp, config, start_tid)

    svar = input("\n🔍 Vill du analysera det här träningsloppet direkt? (j/n): ").strip().lower()
    if svar == "j":
        senaste_video = inspelningar[-1]["fil"]
        starta_analysläge(senaste_video, valt_loppnamn=None, tillåt_nästa_lopp=False)

    svar2 = input("\n➕ Vill du ta tid på ett träningslopp till? (j/n): ").strip().lower()
    if svar2 == "j":
        starta_traningsläge(config)
    else:
        print("🏁 Träningspass avslutat.")
