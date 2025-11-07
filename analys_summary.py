from paths import relativ_sökväg
from textutils import sanera_filnamn

def visa_loggningsstatus(loggade_tider, startlista):
    print("\n📋 Loggningsstatus:")
    for hundnummer in sorted(startlista.keys(), key=int):
        info = startlista.get(hundnummer, {})
        namn = info.get("namn", f"Hund {hundnummer}")
        tider = loggade_tider.get(hundnummer, [])
        status = f"{len(tider)} tider" if tider else "❌"
        print(f"  Hund {hundnummer}: {namn} {status}")
def visa_sammanfattning(loppnamn, loggade_tider, startlista):
    print(f"\n📋 Sammanfattning för {loppnamn}:")
    if not loggade_tider:
        print("⚠️ Inga tider loggade.")
        return

    def extrahera_tider(tider):
        if isinstance(tider, str) and tider == "DNF":
            return []
        if isinstance(tider, list):
            return [
                t["tid"] if isinstance(t, dict) and "tid" in t else t
                for t in tider
                if isinstance(t, (float, int)) or (isinstance(t, dict) and "tid" in t)
            ]
        elif isinstance(tider, dict) and "tid" in tider:
            return [tider["tid"]]
        elif isinstance(tider, (float, int)):
            return [tider]
        return []

    sorterade = sorted(
        loggade_tider.items(),
        key=lambda x: max(extrahera_tider(x[1])) if extrahera_tider(x[1]) else float('inf')
    )

    for placering, (hundnummer, tider) in enumerate(sorterade, start=1):
        info = startlista.get(str(hundnummer), {})
        namn = info.get("namn", f"Hund {hundnummer}")
        klubb = info.get("klubb", "")
        tider_lista = extrahera_tider(tider)
        if tider_lista:
            tider_str = ", ".join(f"{t:.3f}s" for t in sorted(tider_lista))
        else:
            tider_str = "DNF"
        print(f"  {placering}. Hund {hundnummer} ({namn}) {klubb}: {tider_str}")
