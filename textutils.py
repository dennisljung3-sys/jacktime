import unicodedata

def sanera_filnamn(text):
    text = unicodedata.normalize("NFKD", text)
    return "".join(c for c in text if c.isalnum() or c in "_-. ").strip()

def normalisera(text):
    return unicodedata.normalize("NFKD", text).casefold()

def ersätt_svenska_tecken(text):
    return text.replace("å", "a").replace("ä", "a").replace("ö", "o") \
               .replace("Å", "A").replace("Ä", "A").replace("Ö", "O")
