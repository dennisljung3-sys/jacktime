# traning.py
from paths import relativ_sökväg
import os
import datetime
from tidtagning_core import förbered_kamera_och_mållinje
from startsensor import vänta_på_startsignal
from inspelning import kör_inspelningsloop
from metadata import spara_metadata_och_frame_tider
from analys_main import starta_analysläge
from textutils import sanera_filnamn
from fönsterhanterare import get_fönster
from fifo_input import input_från_fifo, skriv_status   # ⭐ NYTT


def skapa_traningsmapp():
    basmapp = relativ_sökväg("träning")
    os.makedirs(basmapp, exist_ok=True)
    datum = datetime.date.today().isoformat()
    dagens_mapp = os.path.join(basmapp, datum)
    if os.path.isfile(dagens_mapp):
        print(
            f"⚠️ En fil med namnet '{dagens_mapp}' blockerar sparning. Ta bort den först."
        )
        return None
    os.makedirs(dagens_mapp, exist_ok=True)
    return dagens_mapp


def starta_traningsläge(config):
    from confighantering import ladda_config, spara_config

    config = ladda_config()

    print("\n🏋️‍♂️ Startar träningsläge...")
    skriv_status("traning_startar", meddelande="Startar träningsläge")

    spara_mapp = skapa_traningsmapp()
    if not spara_mapp:
        skriv_status("fel", meddelande="Kunde inte skapa träningsmapp")
        return

    # OBS: förbered_kamera_och_mållinje returnerar cap från fönsterhanteraren
    cap, metadata = förbered_kamera_och_mållinje(config)
    if cap is None:
        print("❌ Kunde inte förbereda kameran.")
        skriv_status("huvudmeny")
        return

    config["mållinje_x"] = metadata.get("mållinje_x")
    config["skärmstorlek"] = metadata.get("skärmstorlek")

    # ⭐ NYTT: Status innan vi väntar på Enter
    skriv_status(
        "traning_vantar_enter",
        meddelande="Tryck Redo för start när du vill ta emot startsignal",
    )

    input_från_fifo("\n⏳ Tryck [enter] när du är redo att ta emot startsignal...")

    # ⭐ NYTT: Status innan vi väntar på startsignal
    skriv_status(
        "traning_vantar_start",
        meddelande="Väntar på startsignal (Arduino eller Enter)",
    )

    start_tid = vänta_på_startsignal(config["arduino_port"])
    if start_tid is None:
        print("↩️ Tidtagning avbruten – återgår till huvudmenyn.")
        # ⭐ Viktigt: frigör kameran om den är öppen
        fönster = get_fönster()
        if fönster and fönster.kamera_aktiv:
            fönster.koppla_från_kamera()
        skriv_status("huvudmeny")
        return

    tidtagning_str = datetime.datetime.fromtimestamp(start_tid).strftime("%H-%M-%S")
    filnamnsbas = sanera_filnamn(tidtagning_str)

    # ⭐ NYTT: Status innan inspelning börjar
    skriv_status(
        "traning_spelar_in",
        start_tid=start_tid,
        meddelande="Inspelning påbörjad",
    )

    # Använd samma cap som redan är öppen från förbered_kamera_och_mållinje
    inspelningar = kör_inspelningsloop(
        cap, config, start_tid, spara_mapp, filnamnsbas, config["mållinje_x"]
    )

    for insp in inspelningar:
        spara_metadata_och_frame_tider(insp, config, start_tid)

    # ⭐ Viktigt: frigör kameran EFTER inspelningen
    fönster = get_fönster()
    if fönster and fönster.kamera_aktiv:
        fönster.koppla_från_kamera()
        print("📷 Kamera frigjord efter inspelning.")

    # ⭐ NYTT: Status innan analys-frågan
    skriv_status(
        "traning_inspelning_klar",
        antal_inspelningar=len(inspelningar),
        meddelande="Vill du analysera träningsloppet?",
    )

    svar = (
        input_från_fifo("\n🔍 Vill du analysera det här träningsloppet direkt? (j/n): ")
        .strip()
        .lower()
    )
    if svar == "j" and inspelningar:
        senaste_video = inspelningar[-1]["fil"]
        starta_analysläge(senaste_video, valt_loppnamn=None, tillåt_nästa_lopp=False)

    # ⭐ NYTT: Status innan "ett lopp till"-frågan
    skriv_status(
        "traning_fraga_ett_till",
        meddelande="Vill du ta tid på ett träningslopp till?",
    )

    svar2 = (
        input_från_fifo("\n➕ Vill du ta tid på ett träningslopp till? (j/n): ")
        .strip()
        .lower()
    )
    if svar2 == "j":
        # ⭐ Ladda om config för att få eventuella uppdateringar
        config = ladda_config()
        starta_traningsläge(config)
    else:
        print("🏁 Träningspass avslutat.")
        skriv_status("huvudmeny")
