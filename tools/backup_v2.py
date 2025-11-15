import os
import zipfile
from datetime import datetime

# 🔧 Ange sökvägar här
källmapp = os.path.expanduser("/home/dennis/test_git/jacktime")   # ← projektmappen med .py-filer
utfil = os.path.expanduser("/home/dennis/test_git/jacktime/tools")     # ← katalog där zip-filen ska sparas

def hitta_py_filer(mapp):
    return [f for f in os.listdir(mapp) if f.endswith('.py') and os.path.isfile(os.path.join(mapp, f))]

def skapa_zip(filer, källmapp, zip_sökväg):
    with zipfile.ZipFile(zip_sökväg, 'w') as zipf:
        for fil in filer:
            zipf.write(os.path.join(källmapp, fil), arcname=fil)
    print(f"✅ Zip-fil skapad: {zip_sökväg}")

def main():
    svar = input("Vill du säkerhetskopiera projektet nu? (Ja/Nej): ").strip().lower()
    if svar != "ja":
        print("Avslutar programmet.")
        return

    # 🕒 Skapa zip-filnamn med tidsstämpel
    zip_namn = datetime.now().strftime("tidtagning_%Y%m%d_%H%M%S.zip")
    zip_sökväg = os.path.join(utfil, zip_namn)

    filer = hitta_py_filer(källmapp)
    if not filer:
        print("⚠️ Inga .py-filer hittades i mappen.")
        return

    skapa_zip(filer, källmapp, zip_sökväg)

if __name__ == "__main__":
    main()
