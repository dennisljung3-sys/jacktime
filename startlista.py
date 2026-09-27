# startlista.py
from paths import relativ_sökväg
import os
import json
import re
from textutils import sanera_filnamn


def normalisera_loppnamn(startlista):
    """
    Tar bort befintligt loppnummer-prefix och lägger till rätt nummer
    baserat på loppets position i listan.

    Format: "N-Loppnamn" där N är 1-baserat index.

    Exempel:
    - "DennisLoppet" (position 0) → "1-DennisLoppet"
    - "1-DennisLoppet" (position 0) → "1-DennisLoppet"
    - "3-DennisLoppet" (position 2) → "3-DennisLoppet"
    - "1 1 DennisLoppet" (position 0) → "1-DennisLoppet"
    """
    for i, lopp in enumerate(startlista):
        namn = lopp.get("lopp_namn", "").strip()

        # Ta bort eventuellt befintligt prefix (siffra + valfritt separator)
        # Matchar "1-", "12-", "1 ", "12 ", "1. " etc i början
        namn_utan_prefix = re.sub(r"^\d+[\s\-\.]+", "", namn).strip()

        # Om namnet är tomt efter rensning, använd ett standardnamn
        if not namn_utan_prefix:
            namn_utan_prefix = "Lopp"

        # Lägg till rätt loppnummer med bindestreck
        lopp["lopp_namn"] = f"{i + 1}-{namn_utan_prefix}"

    return startlista


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

    # ⭐ NYTT: Normalisera loppnamn innan sparande
    startlista = normalisera_loppnamn(startlista)

    # Visa sammanfattning av vad som sparas
    print("\n📋 Lopp som sparas:")
    for lopp in startlista:
        print(f"  - {lopp['lopp_namn']}")

    with open(filväg, "w", encoding="utf-8") as f:
        json.dump(startlista, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Startlista sparad: {filväg}")
