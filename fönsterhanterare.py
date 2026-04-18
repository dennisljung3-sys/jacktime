# fönsterhanterare.py
import cv2
import os
import json
import time
import numpy as np
from paths import relativ_sökväg


class FönsterHanterare:
    """
    En central fönsterhanterare för hela JackTime.
    Hanterar ETT fönster som återanvänds för alla ändamål.
    """

    def __init__(self):
        self.fönster_namn = "JackTime"
        self.fönster = None
        self.nuvarande_läge = (
            "tom"  # tom, förhandsvisning, tidtagning, analys, kalibrering
        )

        # Standardinställningar
        self.bredd = 800
        self.höjd = 600
        self.x_pos = 100
        self.y_pos = 100

        # Kamera/video-relaterat
        self.cap = None
        self.kamera_aktiv = False
        self.video_aktiv = False

        # Läges-specifik data
        self.läges_data = {}

        # Ladda sparade inställningar
        self._ladda_inställningar()

    def _ladda_inställningar(self):
        """Laddar fönsterposition från config.json"""
        try:
            config_fil = relativ_sökväg("data", "config.json")
            if os.path.exists(config_fil):
                with open(config_fil, "r") as f:
                    config = json.load(f)
                    fönster_config = config.get("fönster", {})
                    self.bredd = fönster_config.get("bredd", 800)
                    self.höjd = fönster_config.get("höjd", 600)
                    self.x_pos = fönster_config.get("x", 100)
                    self.y_pos = fönster_config.get("y", 100)
        except Exception as e:
            print(f"⚠️ Kunde inte ladda fönsterinställningar: {e}")

    def _spara_inställningar(self):
        """Sparar fönsterposition till config.json"""
        try:
            config_fil = relativ_sökväg("data", "config.json")
            config = {}
            if os.path.exists(config_fil):
                with open(config_fil, "r") as f:
                    config = json.load(f)

            if "fönster" not in config:
                config["fönster"] = {}

            config["fönster"]["bredd"] = self.bredd
            config["fönster"]["höjd"] = self.höjd
            config["fönster"]["x"] = self.x_pos
            config["fönster"]["y"] = self.y_pos

            with open(config_fil, "w") as f:
                json.dump(config, f, indent=2)
        except Exception as e:
            print(f"⚠️ Kunde inte spara fönsterinställningar: {e}")

    def skapa_fönster(self):
        """Skapar fönstret med sparad position och storlek"""
        cv2.namedWindow(self.fönster_namn, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(self.fönster_namn, self.bredd, self.höjd)
        cv2.moveWindow(self.fönster_namn, self.x_pos, self.y_pos)
        print(
            f"✅ Fönster skapat: {self.bredd}x{self.höjd} vid ({self.x_pos},{self.y_pos})"
        )

    def visa_startsida(self):
        """Visar en statisk startsida i fönstret - håller fönstret öppet och responsivt"""
        # Skapa en mörkgrå bakgrund
        bild = 50 * np.ones((self.höjd, self.bredd, 3), dtype=np.uint8)

        # Rubrik
        cv2.putText(
            bild,
            "JackTime",
            (self.bredd // 2 - 80, self.höjd // 2 - 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            1.5,
            (0, 255, 0),
            3,
        )

        # Undertext
        cv2.putText(
            bild,
            "Tidtagning for hundkapplopning",
            (self.bredd // 2 - 190, self.höjd // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (200, 200, 200),
            2,
        )

        # Instruktioner
        cv2.putText(
            bild,
            "Anvand terminalmenyn for att starta",
            (self.bredd // 2 - 200, self.höjd // 2 + 50),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (150, 150, 150),
            1,
        )

        # Visa instruktion om att klicka i fönstret
        cv2.putText(
            bild,
            "Klicka i detta fonster for tangentbord",
            (self.bredd // 2 - 200, self.höjd - 30),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (100, 100, 100),
            1,
        )

        cv2.imshow(self.fönster_namn, bild)
        cv2.waitKey(1)  # Viktig: waitKey(1) håller fönstret öppet och lyhört

    def visa_text(self, text, duration=2):
        """Visar en text i fönstret under en kort stund"""
        bild = 100 * np.ones((self.höjd, self.bredd, 3), dtype=np.uint8)

        # Centrera texten
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 1
        thickness = 2
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]
        text_x = (self.bredd - text_size[0]) // 2
        text_y = (self.höjd + text_size[1]) // 2

        cv2.putText(
            bild, text, (text_x, text_y), font, font_scale, (0, 255, 0), thickness
        )
        cv2.imshow(self.fönster_namn, bild)
        cv2.waitKey(int(duration * 1000))
        cv2.waitKey(1)  # Återställ till lyhört läge

    def koppla_kamera(self, kamera_index):
        """Kopplar en kamera till fönstret"""
        try:
            import platform

            if platform.system() == "Windows":
                self.cap = cv2.VideoCapture(kamera_index, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(kamera_index)

            if self.cap.isOpened():
                self.kamera_aktiv = True
                print(f"📷 Kamera {kamera_index} ansluten")
                return True
            else:
                print(f"❌ Kunde inte öppna kamera {kamera_index}")
                return False
        except Exception as e:
            print(f"❌ Fel vid anslutning av kamera: {e}")
            return False

    def koppla_från_kamera(self):
        """Frigör kameran"""
        if self.cap is not None:
            self.cap.release()
            self.cap = None
        self.kamera_aktiv = False
        print("📷 Kamera frånkopplad")

    def ladda_video(self, video_sökväg):
        """Laddar en videofil för analys"""
        try:
            self.cap = cv2.VideoCapture(video_sökväg)
            if self.cap.isOpened():
                self.video_aktiv = True
                print(f"🎞️ Video laddad: {video_sökväg}")
                return True
            else:
                print(f"❌ Kunde inte öppna video: {video_sökväg}")
                return False
        except Exception as e:
            print(f"❌ Fel vid laddning av video: {e}")
            return False

    def byt_läge(self, nytt_läge, **kwargs):
        """Byter läge för fönstret"""
        self.nuvarande_läge = nytt_läge
        self.läges_data.update(kwargs)
        print(f"🔄 Bytte till läge: {nytt_läge}")

    def _hämta_instruktioner(self):
        """Hämtar instruktioner baserat på nuvarande läge"""
        if self.nuvarande_läge == "tidtagning":
            return "🖱️ Klicka här | A/D = flytta mållinje | Mellanslag = start/paus | Q = avsluta"
        elif self.nuvarande_läge == "analys":
            return "🖱️ Klicka här | 1-6 = valj hund | A/D = backa/fram | Q = avsluta"
        elif self.nuvarande_läge == "kalibrering":
            return "🖱️ Klicka här | Q = avbryt kalibrering"
        else:
            return "🖱️ Klicka här for tangentbord"

    def stäng(self):
        """Stänger fönstret och frigör resurser"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()
        print("✅ Fönsterhanterare stängd")


# Global instans för enkel åtkomst från andra moduler
_fönster_instans = None


def get_fönster():
    """Returnerar den globala fönsterhanterar-instansen"""
    global _fönster_instans
    if _fönster_instans is None:
        _fönster_instans = FönsterHanterare()
    return _fönster_instans


def set_fönster(fh):
    """Sätter den globala fönsterhanterar-instansen"""
    global _fönster_instans
    _fönster_instans = fh


# För att testa modulen direkt
if __name__ == "__main__":
    print("🧪 Testar FönsterHanterare...")
    fh = FönsterHanterare()
    fh.skapa_fönster()
    fh.visa_startsida()
    print("✅ Fönstret är öppet. Tryck Ctrl+C i terminalen för att avsluta testet.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        fh.stäng()
        print("✅ Test avslutat")
