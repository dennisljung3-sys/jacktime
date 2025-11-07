from paths import relativ_sökväg
import json
from textutils import sanera_filnamn, normalisera

def ladda_startlista(filnamn):
    """
    Läser in en startlista från en JSON-fil och returnerar en lista med lopp.
    Varje lopp innehåller namn, distans och en filtrerad lista med hundar.
    """
    sökväg = relativ_sökväg("startlistor", sanera_filnamn(filnamn) + ".json")
    try:
        with open(sökväg, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Startlista saknas: {sökväg}")
        return []
    except json.JSONDecodeError:
        print(f"❌ Ogiltigt JSON-format i: {sökväg}")
        return []

    if not isinstance(data, list):
        print("❌ Ogiltigt format – förväntar lista av lopp.")
        return []

    lopp = []
    for entry in data:
        hundar = entry.get("hundar", {})
        filtrerade = [
            {"nummer": int(nr), "namn": namn}
            for nr, namn in hundar.items()
            if namn.strip()
        ]
        if filtrerade:
            lopp.append({
                "lopp_namn": entry.get("lopp_namn", "Okänt"),
                "distans": entry.get("distans", None),
                "hundar": filtrerade
            })
    return lopp
