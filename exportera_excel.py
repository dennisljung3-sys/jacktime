import re

def skapa_filnamn(loppnamn):
    # Ersätt mellanslag med understreck, ta bort specialtecken
    filnamn = loppnamn.strip().lower()
    filnamn = filnamn.replace("å", "a").replace("ä", "a").replace("ö", "o")
    filnamn = re.sub(r"[^\w\s-]", "", filnamn)
    filnamn = re.sub(r"\s+", "_", filnamn)
    return f"{filnamn}.xlsx"
