from paths import relativ_sökväg
import cv2
import json
import os
from textutils import normalisera, sanera_filnamn

def ladda_video_och_metadata(videofil, valt_loppnamn=None):
    if not os.path.exists(videofil):
        print(f"❌ Videofil hittades inte: {videofil}")
        return None, None, None, None, None

    metadata_fil = os.path.splitext(videofil)[0] + ".json"
    if not os.path.exists(metadata_fil):
        print(f"❌ Metadatafil saknas: {metadata_fil}")
        return None, None, None, None, None

    with open(metadata_fil, "r") as f:
        filinnehåll = json.load(f)

    if "metadata" in filinnehåll:
        metadata = filinnehåll["metadata"]
    else:
        metadata = {k: v for k, v in filinnehåll.items() if k not in ["tider", "startlista"]}

    startlista = filinnehåll.get("startlista", {})

    mållinje_x = metadata.get("mållinje_x")
    if mållinje_x is None:
        print("⚠️ Mållinje saknas i metadata – analysen kan bli felaktig.")

    delar = videofil.split(os.sep)
    if len(delar) < 3:
        print("❌ Ogiltig sökväg till videofil.")
        return None, None, None, None, None
    startlista_namn = delar[-2]

    if valt_loppnamn is None:
        print("ℹ️ Träningsläge: ingen startlista används.")
        loppnamn = os.path.splitext(os.path.basename(videofil))[0]
        if not startlista:
            startlista = {
                str(i): {"namn": f"Hund {i}", "klubb": ""}
                for i in range(1, 7)
            }
        cap = cv2.VideoCapture(videofil)
        if not cap.isOpened():
            print("❌ Kunde inte öppna videon.")
            return None, None, None, None, None
        return cap, metadata, startlista, loppnamn, "träning"

    startlista_fil = relativ_sökväg("startlistor", f"{sanera_filnamn(startlista_namn)}.json")
    if not os.path.exists(startlista_fil):
        print(f"❌ Startlista saknas: {startlista_fil}")
        return None, None, None, None, None

    with open(startlista_fil, "r", encoding="utf-8") as f:
        alla_lopp = json.load(f)

    valt_loppnamn = valt_loppnamn.replace("_", " ") if valt_loppnamn else None

    matchande_lopp = next(
        (lopp for lopp in alla_lopp if normalisera(lopp.get("lopp_namn", "")) == normalisera(valt_loppnamn)),
        None
    )
    if not matchande_lopp:
        print(f"❌ Hittade inget lopp med namn '{valt_loppnamn}' i startlistan.")
        return None, None, None, None, None

    loppnamn = matchande_lopp.get("lopp_namn", "Okänt lopp")
    hundar = matchande_lopp.get("hundar", {})
    startlista = {
        str(nr): {"namn": namn, "klubb": ""}
        for nr, namn in hundar.items()
    }

    cap = cv2.VideoCapture(videofil)
    if not cap.isOpened():
        print("❌ Kunde inte öppna videon.")
        return None, None, None, None, None

    return cap, metadata, startlista, loppnamn, startlista_namn
