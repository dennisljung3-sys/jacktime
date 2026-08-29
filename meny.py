from paths import relativ_sökväg
from tavling import starta_tavlingsläge
from traning import starta_traningsläge
from analys_main import starta_analysläge
from startlista import skapa_startlista
from redigera_startlista import redigera_startlista
from installningar_meny import installningsmeny
from sammanfattning import visa_tidigare_sammanfattning, exportera_hel_tävling
from textutils import sanera_filnamn, normalisera
from confighantering import ladda_config, spara_config
import os


def visa_jacktime_logga():
    print(r"""
      ██╗ █████╗  ██████╗██╗  ██╗████████╗██╗███╗   ███╗███████╗
      ██║██╔══██╗██╔════╝██║  ██║╚══██╔══╝██║████╗ ████║██╔════╝
      ██║███████║██║     ███████║   ██║   ██║██╔████╔██║█████╗  
 ██   ██║██╔══██║██║     ██╔══██║   ██║   ██║██║╚██╔╝██║██╔══╝  
 ╚█████╔╝██║  ██║╚██████╗██║  ██║   ██║   ██║██║ ╚═╝ ██║███████╗
  ╚════╝ ╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝╚═╝     ╚═╝╚══════╝
    """)


def huvudmeny():
    if not hasattr(huvudmeny, "visad_logga"):
        visa_jacktime_logga()
        huvudmeny.visad_logga = True
    config = ladda_config()
    print("🐾 Välkommen till JackTime")
    print("📦 Sparade inställningar:")
    print(f"Arduino-port: {config.get('arduino_port')}")
    print(f"Kamera-index: {config.get('kamera_index')}")
    print(
        f"FPS: {config.get('kamera_fps')} (verifierad: {config.get('verifierad_fps')})"
    )
    print(f"Senaste lopp-ID: {config.get('senaste_lopp_id')}\n")

    while True:
        print("🚀 Vad vill du göra?")
        print("1. Starta Tävlingsläge")
        print("2. Starta Träningsläge")
        print("3. Starta analysläge")
        print("4. Skapa startlista")
        print("5. Redigera startlista")
        print("6. Visa resultat och sammanfattningar")
        print("7. Inställningsmeny")
        print("8. Avsluta")
        val = input("👉 Välj (1–8): ").strip()

        if val == "1":
            starta_tavlingsläge(config)
            spara_config(config)

        elif val == "2":
            starta_traningsläge(config)
            spara_config(config)

        elif val == "3":
            visa_analysmeny()

        elif val == "4":
            skapa_startlista()

        elif val == "5":
            redigera_startlista()

        elif val == "6":
            visa_sammanfattningsmeny()

        elif val == "7":
            installningsmeny()
            # Ladda om config EFTER att inställningar är klara
            config = ladda_config()
            print("🔄 Inställningar uppdaterade!")

        elif val == "8":
            print("👋 Avslutar programmet.")
            break

        else:
            print("❌ Ogiltigt val. Försök igen.\n")


def visa_analysmeny():
    from analys_main import starta_analysläge

    print("\n📊 Vad vill du analysera?")
    print("1. Tävling")
    print("2. Träning")
    val_typ = input("👉 Välj (1–2): ").strip()

    if val_typ == "1":
        basmapp = relativ_sökväg("resultat")
        mappar = [
            d
            for d in os.listdir(basmapp)
            if os.path.isdir(os.path.join(basmapp, d)) and d != "träning"
        ]
    elif val_typ == "2":
        basmapp = relativ_sökväg("träning")
        mappar = [
            d for d in os.listdir(basmapp) if os.path.isdir(os.path.join(basmapp, d))
        ]
    else:
        print("❌ Ogiltigt val.")
        return

    if not mappar:
        print("❌ Inga mappar hittades.")
        return

    print("\n📁 Tillgängliga mappar:")
    for i, namn in enumerate(mappar, 1):
        print(f"{i}. {namn}")
    val_mapp = input("👉 Välj (nummer): ").strip()
    if not val_mapp.isdigit() or not (1 <= int(val_mapp) <= len(mappar)):
        print("❌ Ogiltigt val.")
        return
    vald_mapp = mappar[int(val_mapp) - 1]
    full_path = os.path.join(basmapp, vald_mapp)

    videofiler = [f for f in os.listdir(full_path) if f.endswith(".avi")]
    if not videofiler:
        print("❌ Inga videofiler hittades i mappen.")
        return

    loppgrupper = {}
    for f in videofiler:
        delar = f.replace(".avi", "").split("__")
        if len(delar) >= 2:
            prefix = "__".join(delar[:2])
            loppgrupper.setdefault(prefix, []).append(f)

    if not loppgrupper:
        print("❌ Inga giltiga lopp hittades.")
        return

    print(f"\n🏁 Lopp i mappen '{vald_mapp}':")
    loppnamn_lista = list(loppgrupper.keys())
    for i, namn in enumerate(loppnamn_lista, 1):
        delar = namn.split("__")
        if len(delar) == 2:
            lopp_id, lopp_namn = delar
        else:
            lopp_id = namn
            lopp_namn = namn
        print(f"{i}. {lopp_namn} ({lopp_id})")

    val_lopp = input("👉 Välj lopp (nummer): ").strip()
    if not val_lopp.isdigit() or not (1 <= int(val_lopp) <= len(loppnamn_lista)):
        print("❌ Ogiltigt val.")
        return

    valt_prefix = loppnamn_lista[int(val_lopp) - 1]
    matchande_videor = sorted(
        [os.path.join(full_path, f) for f in loppgrupper[valt_prefix]]
    )

    if not matchande_videor:
        print("❌ Inga videor hittades för valt lopp.")
        return

    if val_typ == "2":
        starta_analysläge(
            matchande_videor[0], valt_loppnamn=None, tillåt_nästa_lopp=True
        )
    else:
        loppnamn = valt_prefix.split("__")[1]
        starta_analysläge(
            matchande_videor[0], sanera_filnamn(loppnamn), tillåt_nästa_lopp=True
        )


def visa_sammanfattningsmeny():
    print("\n📊 Vill du visa sammanfattning för:")
    print("1. Tävling")
    print("2. Träning")
    val_typ = input("👉 Välj (1–2): ").strip()

    if val_typ == "1":
        är_träning = False
        basmapp = relativ_sökväg("resultat")
        mappar = [
            d
            for d in os.listdir(basmapp)
            if os.path.isdir(os.path.join(basmapp, d)) and d != "träning"
        ]
    elif val_typ == "2":
        är_träning = True
        basmapp = relativ_sökväg("träning")
        mappar = [
            d for d in os.listdir(basmapp) if os.path.isdir(os.path.join(basmapp, d))
        ]
    else:
        print("❌ Ogiltigt val.")
        return

    if not mappar:
        print(
            f"❌ Inga sparade {'träningspass' if är_träning else 'tävlingar'} hittades."
        )
        return

    print(f"\n📂 Tillgängliga {'träningspass' if är_träning else 'tävlingar'}:")
    for i, namn in enumerate(mappar, 1):
        print(f"  {i}. {namn}")

    val = input("🔢 Välj (nummer): ").strip()
    if not val.isdigit() or int(val) < 1 or int(val) > len(mappar):
        print("❌ Ogiltigt val.")
        return

    vald_mapp = mappar[int(val) - 1]
    full_path = os.path.join(basmapp, vald_mapp)
    alla_filer = os.listdir(full_path)

    def är_giltig_jsonfil(filnamn):
        if not filnamn.endswith(".json"):
            return False
        if (
            "__analys__" in filnamn
            or "__frame_tider" in filnamn
            or "_sammanfattning" in filnamn
        ):
            return False
        return True

    jsonfiler = [f for f in alla_filer if är_giltig_jsonfil(f)]

    if not är_träning:
        avi_basnamn = {os.path.splitext(f)[0] for f in alla_filer if f.endswith(".avi")}
        jsonfiler = [f for f in jsonfiler if os.path.splitext(f)[0] not in avi_basnamn]

    if not jsonfiler:
        print("⚠️ Inga sparade lopp hittades i mappen.")
        return

    print(f"\n📋 Lopp i '{vald_mapp}':")
    for i, fil in enumerate(sorted(jsonfiler), 1):
        print(f"  {i}. {os.path.splitext(fil)[0]}")
    print(
        f"  {len(jsonfiler) + 1}. Exportera hela {'träningspasset' if är_träning else 'tävlingen'} till Excel"
    )

    val2 = input("🔢 Välj lopp eller export (nummer): ").strip()
    if not val2.isdigit():
        print("❌ Ogiltigt val.")
        return

    val2 = int(val2)
    if val2 == len(jsonfiler) + 1:
        exportera_hel_tävling(vald_mapp)
    elif 1 <= val2 <= len(jsonfiler):
        loppnamn = os.path.splitext(sorted(jsonfiler)[val2 - 1])[0]
        visa_tidigare_sammanfattning(
            vald_mapp, sanera_filnamn(loppnamn), är_träning=är_träning
        )
    else:
        print("❌ Ogiltigt val.")
