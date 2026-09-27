from paths import relativ_sökväg
import os
import json
import datetime
import pandas as pd
from textutils import normalisera, sanera_filnamn
from analys_summary import visa_sammanfattning

def exportera_startlista(startlista, filväg):
    filnamn = os.path.basename(filväg).replace(".json", "")
    delar = filnamn.split("_", 1)
    datum = delar[0] if len(delar) > 0 else "Okänt datum"
    tävling = delar[1].replace("_", " ") if len(delar) > 1 else "Okänt tävling"
    export_fil = os.path.join("startlistor", f"{sanera_filnamn(filnamn)}_export.xlsx")

    writer = pd.ExcelWriter(export_fil, engine="openpyxl")

    for i, lopp in enumerate(startlista, start=1):
        rows = []
        for snr in range(1, 7):
            namn = lopp["hundar"].get(str(snr), "")
            rows.append({
                "Startnummer": snr,
                "Namn": namn or "[tom]"
            })
        df = pd.DataFrame(rows)
        sheet_namn = f"Lopp_{i}_{lopp['lopp_namn'][:20]}"
        df.to_excel(writer, sheet_name=sheet_namn[:31], index=False)

    writer.close()
    print(f"\n📝 Export klar: {export_fil}")

def extrahera_sortbar_tid(tider):
    if isinstance(tider, str) and tider == "DNF":
        return float('inf')  # Sorteras sist
    if isinstance(tider, list):
        giltiga = [
            t["tid"] if isinstance(t, dict) and "tid" in t else t
            for t in tider
            if isinstance(t, (float, int)) or (isinstance(t, dict) and "tid" in t)
        ]
        return max(giltiga) if giltiga else float('inf')
    elif isinstance(tider, dict) and "tid" in tider:
        return tider["tid"]
    elif isinstance(tider, (float, int)):
        return tider
    return float('inf')

def formatera_tid(tid):
    if isinstance(tid, (float, int)):
        return f"{tid:.3f}"
    return "DNF"

def visa_sammanfattning(loppnamn, tider, startlista):
    print(f"\n📋 Sammanfattning för {loppnamn}:")
    if not tider:
        print("⚠️ Inga tider loggade.")
        return
    sorterade = sorted(tider.items(), key=lambda x: extrahera_sortbar_tid(x[1]))
    for placering, (hundnummer, tid) in enumerate(sorterade, start=1):
        info = startlista.get(str(hundnummer), {})
        namn = info.get("namn", f"Hund {hundnummer}")
        klubb = info.get("klubb", "")
        if isinstance(tid, list):
            tid_lista = sorted(tid)
            splittid = tid_lista[0]
            måltid = tid_lista[-1]
        else:
            splittid = måltid = tid

        print(f"  {placering}. Hund {hundnummer} ({namn}): Splittid {formatera_tid(splittid)} s, Måltid {formatera_tid(måltid)} s")

def spara_analysresultat(startlista_namn, loppnamn, tider, metadata, startlista):
    mapp = relativ_sökväg("resultat", startlista_namn)
    os.makedirs(mapp, exist_ok=True)
    tidtagning = datetime.datetime.now().strftime("%H-%M-%S")
    filnamn = os.path.join(mapp, f"{sanera_filnamn(loppnamn)}__analys__{tidtagning}.json")

    data = {
        "lopp": loppnamn,
        "tider": tider,
        "metadata": metadata,
        "startlista": startlista
    }

    with open(filnamn, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 Analysresultat sparat: {filnamn}")

def spara_sammanfattning_json(startlista_namn, loppnamn, tider, metadata, startlista):
    if startlista_namn == "träning":
        datum = metadata.get("start_tid", "").split("T")[0] or "okänt_datum"
        mapp = relativ_sökväg("träning", datum)
    else:
        mapp = relativ_sökväg("resultat", startlista_namn)

    os.makedirs(mapp, exist_ok=True)
    filnamn = os.path.join(mapp, f"{sanera_filnamn(loppnamn)}.json")

    data = {
        "tider": tider,
        "metadata": metadata,
        "startlista": startlista
    }

    with open(filnamn, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"💾 Sammanfattning sparad: {filnamn}")

def fråga_om_export(startlista_namn, loppnamn, tider, startlista):
    from fifo_input import input_från_fifo, skriv_status   # ⭐ NYTT

    # ⭐ NYTT: Skriv status till GUI:t
    skriv_status(
        "fraga_om_export",
        lopp=loppnamn,
        meddelande="Vill du exportera sammanfattningen till Excel?",
    )

    svar = input_från_fifo(
        "📤 Vill du exportera sammanfattningen till en Excel-fil? (j/n): "
    ).strip().lower()

    if svar == "j":
        exportera_till_excel(startlista_namn, loppnamn, tider, startlista)

def exportera_till_excel(startlista_namn, loppnamn, tider, startlista):
    if startlista_namn == "träning":
        datum = datetime.date.today().isoformat()
        mapp = relativ_sökväg("träning", datum)
    else:
        mapp = relativ_sökväg("resultat", startlista_namn)

    os.makedirs(mapp, exist_ok=True)
    filnamn = os.path.join(mapp, f"{sanera_filnamn(loppnamn)}_sammanfattning.xlsx")

    def sort_nyckel(item):
        tid = item[1]
        return min(tid) if isinstance(tid, list) else tid

    sorterade = sorted(tider.items(), key=lambda x: extrahera_sortbar_tid(x[1]))
    data = []

    for placering, (hundnummer, tid) in enumerate(sorterade, start=1):
        info = startlista.get(str(hundnummer), {})
        namn = info.get("namn", f"Hund {hundnummer}")

        if isinstance(tid, list):
            tid_lista = sorted(tid)
            splittid = tid_lista[0]
            måltid = tid_lista[-1]
        else:
            splittid = måltid = tid

        data.append({
            "Plats": placering,
            "Startnummer": hundnummer,
            "Namn": namn,
            "Splittid (s)": formatera_tid(splittid),
            "Måltid (s)": formatera_tid(måltid)
        })

    df = pd.DataFrame(data)
    df.to_excel(filnamn, index=False)
    print(f"📊 Excel-fil skapad: {filnamn}")

def visa_tidigare_sammanfattning(datum, loppnamn, startlista=None, är_träning=False):
    """
    Visar sammanfattning för ett tidigare lopp, från tävling eller träning.
    """

    # Välj rätt mapp beroende på typ
    mapptyp = "träning" if är_träning else "resultat"
    sökväg = relativ_sökväg(mapptyp, datum, f"{sanera_filnamn(loppnamn)}.json")

    if not os.path.exists(sökväg):
        print(f"❌ Ingen sparad sammanfattning hittades: {sökväg}")
        return

    try:
        with open(sökväg, "r", encoding="utf-8") as f:
            filinnehåll = json.load(f)
    except json.JSONDecodeError:
        print(f"❌ Ogiltigt JSON-format i: {sökväg}")
        return

    # Hämta tider från "tider"-nyckeln om den finns
    loggade_tider = filinnehåll.get("tider")
    if not loggade_tider:
        # fallback: plocka ut alla nycklar som ser ut som hundnummer
        loggade_tider = {
            k: v for k, v in filinnehåll.items()
            if k.isdigit() and isinstance(v, list)
        }

    # Hämta eller skapa startlista
    startlista = startlista or filinnehåll.get("startlista", {})
    if not startlista:
        hundnummer = sorted(loggade_tider.keys(), key=lambda x: int(x))
        startlista = {
            str(nr): {"namn": f"Hund {nr}", "klubb": ""}
            for nr in hundnummer
        }

    print(f"\n📋 Sammanfattning från fil: {sökväg}")
    visa_sammanfattning(loppnamn, loggade_tider, startlista or {})

def exportera_hel_tävling(startlista_namn):
    import pandas as pd

    träningsmapp = relativ_sökväg("träning", startlista_namn)
    tävlingsmapp = relativ_sökväg("resultat", startlista_namn)

    if os.path.exists(träningsmapp):
        mapp = träningsmapp
        typ = "Träningspass"
    elif os.path.exists(tävlingsmapp):
        mapp = tävlingsmapp
        typ = "Tävling"
    else:
        print(f"❌ Ingen resultatmapp hittades för '{startlista_namn}'")
        return

    alla_filer = os.listdir(mapp)
    jsonfiler = [
        f for f in alla_filer
        if f.endswith(".json")
        and not f.endswith("_sammanfattning.json")
        and "__analys__" not in f
        and "__frame_tider" not in f
    ]

    if not jsonfiler:
        print("❌ Inga resultatfiler hittades.")
        return

    filnamn = relativ_sökväg(mapp, f"{sanera_filnamn(startlista_namn)}_sammanfattning.xlsx")
    writer = pd.ExcelWriter(filnamn, engine="openpyxl")

    alla_rader = []
    alla_rader.append([f"{typ}: {startlista_namn}"])
    alla_rader.append([])

    for fil in sorted(jsonfiler):
        loppnamn = os.path.splitext(fil)[0]
        fullpath = os.path.join(mapp, fil)
        with open(fullpath, "r", encoding="utf-8") as datafil:
            data = json.load(datafil)

        tider = data.get("tider", {})
        if not tider:
            continue

        startlista = data.get("startlista", {
            str(nr): {"namn": f"Hund {nr}"} for nr in tider.keys()
        })

        def sort_nyckel(item):
            tid = item[1]
            return min(tid) if isinstance(tid, list) else tid

        sorterade = sorted(tider.items(), key=lambda x: extrahera_sortbar_tid(x[1]))

        alla_rader.append([f"Lopp: {loppnamn}"])
        alla_rader.append(["Plats", "Startnummer", "Namn", "Splittid (s)", "Måltid (s)"])

        for placering, (hundnummer, tid) in enumerate(sorterade, start=1):
            info = startlista.get(str(hundnummer), {})
            namn = info.get("namn", f"Hund {hundnummer}")
            if isinstance(tid, list):
                tid_lista = sorted(tid)
                splittid = tid_lista[0]
                måltid = tid_lista[-1]
            else:
                splittid = måltid = tid
            alla_rader.append([
                placering,
                hundnummer,
                namn,
                formatera_tid(splittid),
                formatera_tid(måltid)

            ])

        alla_rader.append([])

    df = pd.DataFrame(alla_rader)
    df.to_excel(writer, sheet_name="Sammanfattning", index=False, header=False)
    writer.close()
    print(f"📄 Sammanfattning för hela {typ.lower()} sparad: {filnamn}")
