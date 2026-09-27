#!/usr/bin/env python3
# gui_main.py - JackTime GUI (Tkinter)
#
# Läser status från /tmp/jacktime_status.json och skickar kommandon
# till /tmp/jacktime_input (FIFO). Fungerar parallellt med main.py.
#
# Användning:
#   1. Starta main.py i en terminal
#   2. Starta gui_main.py i en annan terminal

import tkinter as tk
from tkinter import ttk
import json
import os
import time

# === Sökvägar ===
STATUS_PATH = "/tmp/jacktime_status.json"
FIFO_PATH = "/tmp/jacktime_input"

# === Uppdateringsintervall (ms) ===
UPPDATERINGSINTERVALL_MS = 200


# ============================================================
# Kommunikation med terminalen
# ============================================================

def skicka_till_terminal(kommando):
    """Skickar ett kommando till terminalen via FIFO."""
    try:
        with open(FIFO_PATH, "w") as f:
            f.write(kommando + "\n")
        print(f"[GUI →] {kommando!r}")
    except FileNotFoundError:
        print(f"❌ FIFO saknas: {FIFO_PATH} – kör main.py först")
    except Exception as e:
        print(f"❌ Kunde inte skriva till FIFO: {e}")


def läs_status():
    """Läser statusfilen och returnerar en dict, eller None vid fel."""
    if not os.path.exists(STATUS_PATH):
        return None
    try:
        with open(STATUS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Filen kan vara halvskriven precis när vi läser – försök igen nästa gång
        return None


# ============================================================
# Hjälpfunktioner för fönsterplacering
# ============================================================

def beräkna_vänster_halva(root):
    """Returnerar (x, y, bredd, höjd) för vänster halva av skärmen."""
    screen_w = root.winfo_screenwidth()
    screen_h = root.winfo_screenheight()

    # Halva bredden, lite marginal
    bredd = screen_w // 2 - 20
    höjd = screen_h - 100
    x = 10
    y = 40  # lite marginal från toppen

    return x, y, bredd, höjd


# ============================================================
# GUI-klassen
# ============================================================

class JackTimeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JackTime – Kontrollpanel")

        # Placera fönstret på vänster halva
        x, y, bredd, höjd = beräkna_vänster_halva(root)
        self.root.geometry(f"{bredd}x{höjd}+{x}+{y}")

        # Stäng av "always on top" – vi vill inte tvinga oss fram
        self.root.attributes("-topmost", False)

        # Hantera fönsterstängning
        self.root.protocol("WM_DELETE_WINDOW", self.avsluta)

        # Behållare för dynamiskt innehåll
        self.innehållsram = tk.Frame(self.root)
        self.innehållsram.pack(fill="both", expand=True, padx=20, pady=20)

        # Statusrad längst ner
        self.status_var = tk.StringVar(value="🟡 Väntar på anslutning...")
        self.status_label = tk.Label(
            self.root,
            textvariable=self.status_var,
            bd=1,
            relief="sunken",
            anchor="w",
            font=("Arial", 10),
        )
        self.status_label.pack(side="bottom", fill="x")

        # Kom ihåg senaste läge så vi bara bygger om när det ändras
        self.senaste_läge = None
        self.senaste_status = None

        # Starta statusuppdateringen
        self.uppdatera_status()

    # --------------------------------------------------------
    # Huvudloop – läser status och bygger om vid behov
    # --------------------------------------------------------

    def uppdatera_status(self):
        status = läs_status()

        if status is None:
            self.status_var.set("🔴 Ingen anslutning till terminalen")
            self.visa_vantar("Starta main.py i en terminal")
        else:
            läge = status.get("läge", "okänt")

            # Uppdatera endast om statusen har ändrats
            if läge != self.senaste_läge:
                self.senaste_läge = läge
                self.bygg_layout(status)

            # Uppdatera statusraden varje gång
            meddelande = status.get("meddelande", "")
            if meddelande:
                self.status_var.set(f"🟢 {meddelande}")
            else:
                self.status_var.set(f"🟢 {läge}")

        # Schemalägg nästa uppdatering
        self.root.after(UPPDATERINGSINTERVALL_MS, self.uppdatera_status)

    # --------------------------------------------------------
    # Layout-hantering
    # --------------------------------------------------------

    def rensa_innehåll(self):
        """Tar bort alla widgets i innehållsramen."""
        for widget in self.innehållsram.winfo_children():
            widget.destroy()

    def visa_vantar(self, text):
        """Visar en enkel väntar-skärm."""
        self.rensa_innehåll()
        tk.Label(
            self.innehållsram,
            text="🐾 JackTime",
            font=("Arial", 24, "bold"),
        ).pack(pady=20)
        tk.Label(
            self.innehållsram,
            text=text,
            font=("Arial", 12),
            fg="gray",
        ).pack(pady=10)

    def bygg_layout(self, status):
        """Bygger layout baserat på status."""
        läge = status.get("läge", "okänt")

        if läge == "huvudmeny":
            self.bygg_huvudmeny(status)
        elif läge == "avslutad":
            self.visa_vantar("Programmet har avslutats")
        else:
            # Alla andra lägen – visa en tillfällig skärm
            # (vi bygger ut dessa i senare steg)
            self.visa_vantar(f"Läge: {läge} (byggs i nästa steg)")

    # --------------------------------------------------------
    # Huvudmeny
    # --------------------------------------------------------

    def bygg_huvudmeny(self, status):
        self.rensa_innehåll()

        # Rubrik
        tk.Label(
            self.innehållsram,
            text="🐾 JackTime",
            font=("Arial", 24, "bold"),
        ).pack(pady=(0, 5))

        tk.Label(
            self.innehållsram,
            text="Tidtagning för hundkapplöpning",
            font=("Arial", 11),
            fg="gray",
        ).pack(pady=(0, 15))

        ttk.Separator(self.innehållsram, orient="horizontal").pack(fill="x", pady=10)

        # Status-rad (kamera, Arduino)
        kamera = status.get("kamera_index")
        arduino = status.get("arduino_port")
        fps = status.get("kamera_fps")

        status_text = (
            f"📷 Kamera: {'index ' + str(kamera) if kamera is not None else 'Ej vald'}    "
            f"🔌 Arduino: {arduino or 'Ej vald'}    "
            f"🎞️ FPS: {fps or '–'}"
        )
        tk.Label(
            self.innehållsram,
            text=status_text,
            font=("Arial", 9),
            fg="gray",
        ).pack(pady=(0, 10))

        ttk.Separator(self.innehållsram, orient="horizontal").pack(fill="x", pady=10)

        # Menyknappar
        menyval = status.get("menyval", [])
        if not menyval:
            # Fallback om terminalen inte har skickat menyval
            menyval = [
                {"nr": 1, "text": "Starta Tävlingsläge", "emoji": "🏁"},
                {"nr": 2, "text": "Starta Träningsläge", "emoji": "🏋️"},
                {"nr": 3, "text": "Starta analysläge", "emoji": "📊"},
                {"nr": 4, "text": "Skapa startlista", "emoji": "📝"},
                {"nr": 5, "text": "Redigera startlista", "emoji": "✏️"},
                {"nr": 6, "text": "Visa resultat och sammanfattningar", "emoji": "📈"},
                {"nr": 7, "text": "Inställningsmeny", "emoji": "⚙️"},
                {"nr": 8, "text": "Avsluta", "emoji": "🚪"},
            ]

        for val in menyval:
            nr = val["nr"]
            text = val["text"]
            emoji = val.get("emoji", "")

            knapp_text = f"{emoji}  {text}" if emoji else text

            # Färgkodning för olika knappar
            if nr == 1:
                bg = "#4CAF50"
                fg = "white"
            elif nr == 2:
                bg = "#2196F3"
                fg = "white"
            elif nr == 3:
                bg = "#FF9800"
                fg = "white"
            elif nr == 8:
                bg = "#f44336"
                fg = "white"
            else:
                bg = "#e0e0e0"
                fg = "black"

            knapp = tk.Button(
                self.innehållsram,
                text=knapp_text,
                font=("Arial", 12),
                bg=bg,
                fg=fg,
                height=2,
                anchor="w",
                padx=15,
                command=lambda n=nr: self.skicka_val(n),
            )
            knapp.pack(fill="x", pady=4)

    # --------------------------------------------------------
    # Knapptryck
    # --------------------------------------------------------

    def skicka_val(self, nr):
        """Skickar ett menyval till terminalen."""
        skicka_till_terminal(str(nr))

    # --------------------------------------------------------
    # Avsluta
    # --------------------------------------------------------

    def avsluta(self):
        """Stänger GUI:t utan att stänga terminalen."""
        print("👋 Stänger GUI:t (terminalen fortsätter köra)")
        self.root.destroy()


# ============================================================
# Huvudprogram
# ============================================================

def main():
    root = tk.Tk()
    app = JackTimeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
