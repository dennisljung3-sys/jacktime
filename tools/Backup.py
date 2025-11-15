import os
import zipfile
from datetime import datetime

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

    # 🔧 Ange sökvägen till din projektmapp här
    projektmapp = "/home/dennis/VScode/jacktime"  # ← byt ut till din faktiska mapp

    # 📁 Hämta sökväg till skrivbordet
    skrivbord = os.path.join(os.path.expanduser("~"), "Skrivbord/Backup")

    # 🕒 Skapa zip-filnamn med tidsstämpel
    zip_namn = datetime.now().strftime("tidtagning_%Y%m%d_%H%M%S.zip")
    zip_sökväg = os.path.join(skrivbord, zip_namn)

    filer = hitta_py_filer(projektmapp)
    if not filer:
        print("⚠️ Inga .py-filer hittades i mappen.")
        return

    skapa_zip(filer, projektmapp, zip_sökväg)

if __name__ == "__main__":
    main()
