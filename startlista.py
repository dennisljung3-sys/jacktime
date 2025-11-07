from paths import relativ_sökväg
import os
import json
from textutils import sanera_filnamn

def välj_månad():
    månader = [
        "Januari", "Februari", "Mars", "April", "Maj", "Juni",
        "Juli", "Augusti", "September", "Oktober", "November", "December"
    ]
    print("\n📅 Välj månad:")
    for i, månad in enumerate(månader, start=1):
        print(f"{i}. {månad}")
    while True:
        try:
            val = int(input("👉 Nummer (1–12): "))
            if 1 <= val <= 12:
                return val, månader[val - 1]
        except ValueError:
            pass
        print("❌ Ogiltigt val. Försök igen.")

def mata_in_lopp():
    while True:
        lopp_namn = input("\n🏁 Loppets namn: ").strip()
        distans = input("📏 Distans i meter: ").strip()
        hundar = {}

        print("🐶 Ange namn på hundar (startnummer 1–6):")
        for i in range(1, 7):
            namn = input(f"  Startnummer {i}: ").strip()
            if namn:
                hundar[str(i)] = namn

        print("\n📋 Sammanställning:")
        print(f"Lopp: {lopp_namn}")
        print(f"Distans: {distans} meter")
        for i in range(1, 7):
            print(f"  {i}: {hundar.get(str(i), '[tom]')}")

        korrekt = input("\n✅ Är detta korrekt? (j/n): ").strip().lower()
        if korrekt == "j":
            return {
                "lopp_namn": lopp_namn,
                "distans": int(distans) if distans.isdigit() else distans,
                "hundar": hundar
            }
        else:
            print("🔄 Mata in loppet igen.")

def skapa_startlista():
    print("\n🆕 Skapa startlista")

    år = input("📆 Ange år (t.ex. 2025): ").strip()
    månad_nummer, månad_namn = välj_månad()
    dag = input("📆 Ange dag i månaden (t.ex. 11): ").strip()

    namn = input("🏁 Vad vill du kalla tävlingen?: ").strip()
    namn_sanitiserat = sanera_filnamn(namn)

    filnamn = f"{år}-{månad_nummer:02d}-{dag}_{namn_sanitiserat}.json"
    filväg = relativ_sökväg("startlistor", filnamn)
    os.makedirs(os.path.dirname(filväg), exist_ok=True)

    print(f"\n📁 Startlista kommer sparas som: {filväg}")

    startlista = []
    while True:
        lopp = mata_in_lopp()
        startlista.append(lopp)
        fler = input("\n➕ Vill du lägga till ett lopp till? (j/n): ").strip().lower()
        if fler != "j":
            break

    with open(filväg, "w", encoding="utf-8") as f:
        json.dump(startlista, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Startlista sparad: {filväg}")
