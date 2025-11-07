from paths import relativ_sökväg
import os
import json
import datetime
from textutils import sanera_filnamn

def spara_metadata_och_frame_tider(inspelningsinfo, config, start_tid):
    """
    Sparar metadata och frame_tider till .json och .csv för en inspelning.
    """
    metadata = {
        "fps": round(config.get("verifierad_fps", 0), 2),
        "vald_fps": config.get("kamera_fps"),
        "fördröjning": round(inspelningsinfo["starttid"] - start_tid, 6),
        "start_tid": datetime.datetime.fromtimestamp(start_tid).isoformat(),
        "mållinje_x": config.get("mållinje_x"),
        "kamera_index": config.get("kamera_index"),
        "lopp_index": inspelningsinfo.get("lopp_index"),
        "lopp_namn": inspelningsinfo.get("lopp_namn"),
        "inspelningsnummer": inspelningsinfo.get("inspelningsnummer"),
        "tidtagning_start": datetime.datetime.fromtimestamp(start_tid).isoformat()
    }

    if inspelningsinfo.get("frame_tider"):
        metadata["frame_tider"] = inspelningsinfo["frame_tider"]
        csv_fil = inspelningsinfo["fil"].replace(".avi", "_frame_tider.csv")
        csv_fil = os.path.join(os.path.dirname(csv_fil), f"{sanera_filnamn(os.path.basename(csv_fil))}")
        with open(csv_fil, "w") as f:
            for t in inspelningsinfo["frame_tider"]:
                f.write(f"{t:.6f}\n")
        print(f"🧮 Frame-tider sparade: {len(inspelningsinfo['frame_tider'])} st → {os.path.basename(csv_fil)}")

    metadata_fil = inspelningsinfo["fil"].replace(".avi", ".json")
    metadata_fil = os.path.join(os.path.dirname(metadata_fil), f"{sanera_filnamn(os.path.basename(metadata_fil))}")
    with open(metadata_fil, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)
    print(f"📝 Metadata sparad: {os.path.basename(metadata_fil)}")
