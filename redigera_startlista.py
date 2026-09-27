# redigera_startlista.py
from paths import relativ_sökväg
import os
import json
from startlista import mata_in_lopp, normalisera_loppnamn
from gemensamt import ladda_startlista
from textutils import sanera_filnamn, normalisera


def lista_startlistor():
    basmapp = relativ_sökväg("startlistor")
    filer = [f for f in os.listdir(basmapp) if f.endswith(".json")]
    if not filer:
        print("❌ Inga startlistor hittades.")
        return None
    print("\n📁 Tillgängliga startlistor:")
    for i, fil in enumerate(filer, start=1):
        print(f"{i}. {fil}")
    while True:
        try:
            val = int(input("👉 Välj en fil att redigera: "))
            if 1 <= val <= len(filer):
                return relativ_sökväg("startlistor", filer[val - 1])
        except ValueError:
            pass
        print("❌ Ogiltigt val. Försök igen.")


def visa_lopp(startlista):
    print("\n📋 Lopp i startlistan:")
    for i, lopp in enumerate(startlista, start=1):
        print(f"\n{i}. 🏁 {lopp['lopp_namn']} – 📏 {lopp['distans']} meter")
        print("   🐶 Startlista:")
        for snr in range(1, 7):
            namn = lopp["hundar"].get(str(snr), "")
            print(f"     {snr}: {namn or '[tom]'}")


def redigera_lopp(startlista):
    visa_lopp(startlista)
    try:
        val = int(input("✏️ Välj lopp att redigera (nummer): "))
        if 1 <= val <= len(startlista):
            nytt_lopp = mata_in_lopp()
            startlista[val - 1] = nytt_lopp
            # ⭐ NYTT: Normalisera efter ändring
            normalisera_loppnamn(startlista)
            print("✅ Lopp uppdaterat.")
    except:
        print("❌ Ogiltigt val.")


def ta_bort_lopp(startlista):
    visa_lopp(startlista)
    try:
        val = int(input("🗑️ Välj lopp att ta bort (nummer): "))
        if 1 <= val <= len(startlista):
            bekräfta = input(f"⚠️ Ta bort '{startlista[val - 1]['lopp_namn']}'? (j/n): ").lower()
            if bekräfta == "j":
                startlista.pop(val - 1)
                # ⭐ NYTT: Normalisera efter borttagning
                normalisera_loppnamn(startlista)
                print("✅ Lopp borttaget.")
    except:
        print("❌ Ogiltigt val.")


def lägg_till_lopp(startlista):
    nytt_lopp = mata_in_lopp()
    print("\n📌 Var vill du lägga till loppet?")
    print("1. Sist")
    print("2. Före ett annat lopp")
    val = input("👉 Välj (1–2): ").strip()
    if val == "1":
        startlista.append(nytt_lopp)
        print("✅ Lopp tillagt sist.")
    elif val == "2":
        visa_lopp(startlista)
        try:
            index = int(input("📍 Lägg till före lopp nummer: "))
            if 1 <= index <= len(startlista):
                startlista.insert(index - 1, nytt_lopp)
                print(f"✅ Lopp tillagt före lopp {index}.")
        except:
            print("❌ Ogiltigt val.")

    # ⭐ NYTT: Normalisera efter tillägg
    normalisera_loppnamn(startlista)


def exportera_startlista(startlista, filväg):
    filnamn = os.path.basename(filväg).replace(".json", "")
    export_fil = relativ_sökväg("startlistor", f"{sanera_filnamn(filnamn)}_export.txt")
    delar = filnamn.split("_", 1)
    datum = delar[0] if len(delar) > 0 else "Okänt datum"
    tävling = delar[1].replace("_", " ") if len(delar) > 1 else "Okänt tävling"

    with open(export_fil, "w", encoding="utf-8") as f:
        f.write(f"Tävling: {tävling}\n")
        f.write(f"Datum: {datum}\n")
        f.write("=" * 40 + "\n\n")
        for i, lopp in enumerate(startlista, start=1):
            f.write(f"Lopp {i}: {lopp['lopp_namn']} – {lopp['distans']} meter\n")
            for snr in range(1, 7):
                namn = lopp["hundar"].get(str(snr), "")
                f.write(f"  Startnummer {snr}: {namn or '[tom]'}\n")
            f.write("\n")
    print(f"\n📝 Export klar: {export_fil}")


def redigera_startlista():
    filväg = lista_startlistor()
    if not filväg:
        return

    with open(filväg, "r", encoding="utf-8") as f:
        startlista = json.load(f)

    # ⭐ NYTT: Normalisera direkt när filen laddas (fixar gamla startlistor)
    normalisera_loppnamn(startlista)

    while True:
        print("\n🛠️ Vad vill du göra?")
        print("1. Redigera ett lopp")
        print("2. Ta bort ett lopp")
        print("3. Lägg till ett nytt lopp")
        print("4. Visa alla lopp")
        print("5. Exportera till textfil")
        print("6. Spara och avsluta")
        print("7. Avbryt utan att spara")
        val = input("👉 Välj (1–7): ").strip()

        if val == "1":
            redigera_lopp(startlista)
        elif val == "2":
            ta_bort_lopp(startlista)
        elif val == "3":
            lägg_till_lopp(startlista)
        elif val == "4":
            visa_lopp(startlista)
        elif val == "5":
            exportera_startlista(startlista, filväg)
        elif val == "6":
            # ⭐ NYTT: Säkerställ normalisering innan sparande
            normalisera_loppnamn(startlista)
            with open(filväg, "w", encoding="utf-8") as f:
                json.dump(startlista, f, indent=2, ensure_ascii=False)
            print(f"💾 Ändringar sparade till {filväg}")

            # Visa hur loppen sparades
            print("\n📋 Sparade loppnamn:")
            for lopp in startlista:
                print(f"  - {lopp['lopp_namn']}")
            break
        elif val == "7":
            print("❌ Inga ändringar sparades.")
            break
        else:
            print("❌ Ogiltigt val.")
