from paths import relativ_sökväg
import json
import os

CONFIGFIL = relativ_sökväg("data/config.json")

def ladda_config():
    if os.path.exists(CONFIGFIL):
        try:
            with open(CONFIGFIL, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print("⚠️ Fel i config.json – laddar standardvärden.")
    else:
        print("📁 Ingen config-fil hittad – laddar standardvärden.")

    return {
        "kamera_index": None,
        "kamera_fps": None,
        "verifierad_fps": None,
        "arduino_port": None,
        "senaste_lopp_id": 1
    }

def spara_config(config):
    try:
        with open(CONFIGFIL, "w") as f:
            json.dump(config, f, indent=2)
        print("💾 Inställningar sparade.")
    except Exception as e:
        print(f"❌ Kunde inte spara config: {e}")
