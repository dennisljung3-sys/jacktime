import os
import datetime
from tidtagning_core import förbered_kamera_och_mållinje
from startsensor import vänta_på_startsignal
from inspelning import kör_inspelningsloop
from metadata import spara_metadata_och_frame_tider
from analys_main import starta_analysläge
from gemensamt import ladda_startlista
from textutils import sanera_filnamn
from fifo_input import input_från_fifo, skriv_status   # ⭐ NYTT


def välj_startlista():
    filer = [f for f in os.listdir("startlistor") if f.endswith(".json")]
    if not filer:
        print("❌ Inga startlistor hittades.")
        skriv_status("fel", meddelande="Inga startlistor hittades")
        return None

    print("\n📁 Tillgängliga startlistor:")
    for i, fil in enumerate(filer, 1):
        print(f"{i}. {fil}")

    # ⭐ NYTT: Skriv status till GUI:t
    skriv_status(
        "tavling_valj_startlista",
        startlistor=[f for f in filer],
        meddelande="Välj startlista",
    )

    val = input_från_fifo("👉 Välj startlista (nummer): ").strip()
    if not val.isdigit() or not (1 <= int(val) <= len(filer)):
        print("❌ Ogiltigt val.")
        return None
    return os.path.splitext(filer[int(val) - 1])[0]


def välj_lopp(startlista):
    print("\n🏁 Tillgängliga lopp:")
    for i, lopp in enumerate(startlista, 1):
        print(f"{i}. {lopp['lopp_namn']} ({len(lopp['hundar'])} hundar)")

    # ⭐ NYTT: Skriv status till GUI:t
    skriv_status(
        "tavling_valj_lopp",
        lopp=[
            {"nr": i, "namn": l["lopp_namn"], "antal_hundar": len(l["hundar"])}
            for i, l in enumerate(startlista, 1)
        ],
        meddelande="Välj lopp",
    )

    val = input_från_fifo("👉 Välj lopp (nummer): ").strip()
    if not val.isdigit() or not (1 <= int(val) <= len(startlista)):
        print("❌ Ogiltigt val.")
        return None, None
    index = int(val) - 1
    return startlista[index], index


def starta_tavlingsläge(
    config,
    startlista_namn=None,
    startlista=None,
    lopp_index=None,
    hoppa_fortsättningsfråga=False,
):
    from confighantering import ladda_config

    config = ladda_config()

    print("\n🏁 Startar tävlingsläge...")
    skriv_status("tavling_startar", meddelande="Startar tävlingsläge")

    if not startlista_namn:
        startlista_namn = välj_startlista()
        if not startlista_namn:
            skriv_status("huvudmeny")
            return

    if not startlista:
        startlista = ladda_startlista(startlista_namn)
        if not startlista:
            print("❌ Startlistan är tom eller ogiltig.")
            skriv_status("huvudmeny")
            return

    if lopp_index is None:
        valt_lopp, lopp_index = välj_lopp(startlista)
        if not valt_lopp:
            skriv_status("huvudmeny")
            return
    else:
        valt_lopp = startlista[lopp_index]

    spara_mapp = os.path.join("resultat", sanera_filnamn(startlista_namn))
    if os.path.isfile(spara_mapp):
        print(
            f"⚠️ En fil med namnet '{spara_mapp}' blockerar sparning. Ta bort den först."
        )
        skriv_status("fel", meddelande="En fil blockerar sparning")
        return
    os.makedirs(spara_mapp, exist_ok=True)

    # ⭐ NYTT: Skriv status om valt lopp
    skriv_status(
        "tavling_redo",
        startlista=startlista_namn,
        lopp=valt_lopp["lopp_namn"],
        lopp_index=lopp_index + 1,
        antal_lopp=len(startlista),
        meddelande=f"Redo för {valt_lopp['lopp_namn']}",
    )

    cap, metadata = förbered_kamera_och_mållinje(config)
    config["mållinje_x"] = metadata.get("mållinje_x")
    config["skärmstorlek"] = metadata.get("skärmstorlek")

    # ⭐ NYTT: Skriv status innan vi väntar på Enter
    skriv_status(
        "tavling_vantar_enter",
        lopp=valt_lopp["lopp_namn"],
        meddelande="Tryck Redo för start när du vill ta emot startsignal",
    )

    input_från_fifo("\n⏳ Tryck [enter] när du är redo att ta emot startsignal...")

    # ⭐ NYTT: Skriv status innan vi väntar på startsignal
    skriv_status(
        "tavling_vantar_start",
        lopp=valt_lopp["lopp_namn"],
        meddelande="Väntar på startsignal (Arduino eller Enter)",
    )

    start_tid = vänta_på_startsignal(config["arduino_port"])
    if start_tid is None:
        print("↩️ Tidtagning avbruten – återgår till huvudmenyn.")
        skriv_status("huvudmeny")
        return

    tidtagning_str = datetime.datetime.fromtimestamp(start_tid).strftime("%H-%M-%S")
    loppnamn_rensad = sanera_filnamn(valt_lopp["lopp_namn"])
    filnamnsbas = f"Lopp-{lopp_index + 1}__{loppnamn_rensad}__{tidtagning_str}"

    # ⭐ NYTT: Skriv status innan inspelning börjar
    skriv_status(
        "tavling_spelar_in",
        lopp=valt_lopp["lopp_namn"],
        start_tid=start_tid,
        meddelande="Inspelning påbörjad",
    )

    inspelningar = kör_inspelningsloop(
        cap, config, start_tid, spara_mapp, filnamnsbas, config["mållinje_x"]
    )

    for insp in inspelningar:
        insp["lopp_index"] = lopp_index + 1
        insp["lopp_namn"] = valt_lopp["lopp_namn"]
        spara_metadata_och_frame_tider(insp, config, start_tid)

    # ⭐ NYTT: Skriv status när inspelningen är klar
    skriv_status(
        "tavling_inspelning_klar",
        lopp=valt_lopp["lopp_namn"],
        antal_inspelningar=len(inspelningar),
        meddelande="Vill du analysera loppet?",
    )

    svar = input_från_fifo(
        "\n🔍 Vill du analysera det här loppet direkt? (j/n): "
    ).strip().lower()
    if svar == "j":
        senaste_video = inspelningar[-1]["fil"]
        starta_analysläge(
            videofil=senaste_video,
            valt_loppnamn=valt_lopp["lopp_namn"],
            tillåt_nästa_lopp=True,
            startlista_namn=startlista_namn,
            startlista=startlista,
            lopp_index=lopp_index,
        )

    if not hoppa_fortsättningsfråga:
        # ⭐ NYTT: Skriv status innan nästa-lopp-frågan
        skriv_status(
            "tavling_fraga_nasta",
            lopp=valt_lopp["lopp_namn"],
            nästa_lopp=(
                startlista[lopp_index + 1]["lopp_namn"]
                if lopp_index + 1 < len(startlista)
                else None
            ),
            meddelande="Vill du ta tid i nästa lopp?",
        )

        svar2 = input_från_fifo("\n⏭️ Vill du ta tid i nästa lopp? (j/n): ").strip().lower()
        if svar2 == "j" and lopp_index + 1 < len(startlista):
            config["senaste_lopp_id"] = lopp_index + 2
            nästa_lopp = startlista[lopp_index + 1]
            print(f"\n⏱️ Nästa lopp: {nästa_lopp['lopp_namn']}")
            starta_tavlingsläge(config, startlista_namn, startlista, lopp_index + 1)
        else:
            print("🏁 Tävlingspass avslutat.")
            skriv_status("huvudmeny")
