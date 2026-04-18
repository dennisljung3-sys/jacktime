#!/usr/bin/env python3
# gui_enkel.py - Enkel GUI för JackTime

import tkinter as tk
from tkinter import ttk, messagebox
import threading
import os
import sys

# Lägg till projektets sökväg för att kunna importera moduler
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from confighantering import ladda_config, spara_config
from fönsterhanterare import get_fönster, set_fönster, FönsterHanterare


class JackTimeGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("JackTime - Tidtagning för hundkapplöpning")
        self.root.geometry("500x550")
        self.root.resizable(False, False)

        # Försök sätta ikon (om den finns)
        try:
            self.root.iconbitmap("icon.ico")
        except:
            pass

        # Ladda config
        self.config = ladda_config()

        # Skapa fönsterhanteraren om den inte redan finns
        fönster = get_fönster()
        if fönster is None or fönster.fönster_namn is None:
            fönster = FönsterHanterare()
            fönster.skapa_fönster()
            set_fönster(fönster)
            fönster.visa_startsida()

        self.skapa_widgets()
        self.uppdatera_status()

    def skapa_widgets(self):
        # Rubrik
        titel = tk.Label(self.root, text="JackTime", font=("Arial", 24, "bold"))
        titel.pack(pady=15)

        undertext = tk.Label(
            self.root, text="Tidtagning för hundkapplöpning", font=("Arial", 12)
        )
        undertext.pack(pady=5)

        # Separator
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10, padx=20)

        # Statusram
        status_ram = tk.LabelFrame(self.root, text="Status", padx=10, pady=5)
        status_ram.pack(fill="x", padx=20, pady=5)

        self.kamera_status = tk.Label(status_ram, text="Kamera: Ej vald", anchor="w")
        self.kamera_status.pack(fill="x")

        self.arduino_status = tk.Label(status_ram, text="Arduino: Ej vald", anchor="w")
        self.arduino_status.pack(fill="x")

        self.fps_status = tk.Label(status_ram, text="FPS: Ej vald", anchor="w")
        self.fps_status.pack(fill="x")

        # Huvudknappar
        knapp_ram = tk.Frame(self.root)
        knapp_ram.pack(pady=15)

        # Tävlingsläge
        self.tavling_btn = tk.Button(
            knapp_ram,
            text="🏁 Tävlingsläge",
            font=("Arial", 12),
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2,
            command=self.starta_tavling,
        )
        self.tavling_btn.pack(pady=5)

        # Träningsläge
        self.traning_btn = tk.Button(
            knapp_ram,
            text="🏋️ Träningsläge",
            font=("Arial", 12),
            bg="#2196F3",
            fg="white",
            width=20,
            height=2,
            command=self.starta_traning,
        )
        self.traning_btn.pack(pady=5)

        # Analysläge
        self.analys_btn = tk.Button(
            knapp_ram,
            text="📊 Analysläge",
            font=("Arial", 12),
            bg="#FF9800",
            fg="white",
            width=20,
            height=2,
            command=self.starta_analys,
        )
        self.analys_btn.pack(pady=5)

        # Separator
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10, padx=20)

        # Inställningsknappar
        inst_ram = tk.Frame(self.root)
        inst_ram.pack(pady=5)

        self.kamera_btn = tk.Button(
            inst_ram, text="📷 Välj kamera", width=15, command=self.valj_kamera
        )
        self.kamera_btn.pack(side="left", padx=5)

        self.arduino_btn = tk.Button(
            inst_ram, text="🔌 Välj Arduino", width=15, command=self.valj_arduino
        )
        self.arduino_btn.pack(side="left", padx=5)

        self.kalibrera_btn = tk.Button(
            inst_ram, text="⚡ Kalibrera", width=15, command=self.kalibrera
        )
        self.kalibrera_btn.pack(side="left", padx=5)

        # Separator
        ttk.Separator(self.root, orient="horizontal").pack(fill="x", pady=10, padx=20)

        # Avsluta
        self.avsluta_btn = tk.Button(
            self.root,
            text="Avsluta",
            font=("Arial", 10),
            bg="#f44336",
            fg="white",
            width=15,
            command=self.avsluta,
        )
        self.avsluta_btn.pack(pady=10)

        # Statusfält längst ner
        self.status_var = tk.StringVar(value="Redo")
        status_falt = tk.Label(
            self.root, textvariable=self.status_var, bd=1, relief="sunken", anchor="w"
        )
        status_falt.pack(side="bottom", fill="x", padx=5, pady=5)

    def uppdatera_status(self):
        """Uppdaterar statusvisningen"""
        config = ladda_config()

        kamera = config.get("kamera_index")
        if kamera is not None:
            self.kamera_status.config(text=f"Kamera: Index {kamera}")
        else:
            self.kamera_status.config(text="Kamera: Ej vald")

        arduino = config.get("arduino_port")
        if arduino:
            self.arduino_status.config(text=f"Arduino: {arduino}")
        else:
            self.arduino_status.config(text="Arduino: Ej vald")

        fps = config.get("kamera_fps")
        verifierad = config.get("verifierad_fps")
        if fps:
            self.fps_status.config(text=f"FPS: {fps} (verifierad: {verifierad})")
        else:
            self.fps_status.config(text="FPS: Ej vald")

        # Uppdatera var 2:e sekund
        self.root.after(2000, self.uppdatera_status)

    def satt_status(self, text, duration=2):
        """Sätter tillfällig status text"""
        self.status_var.set(text)
        self.root.after(duration * 1000, lambda: self.status_var.set("Redo"))

    def starta_tavling(self):
        """Startar tävlingsläge i separat tråd"""
        config = ladda_config()

        if config.get("kamera_index") is None:
            messagebox.showerror(
                "Fel", "Välj kamera först! (Inställningar → Välj kamera)"
            )
            return

        if config.get("arduino_port") is None:
            svar = messagebox.askyesno(
                "Varning",
                "Ingen Arduino vald. Vill du fortsätta med manuell start (Enter)?",
            )
            if not svar:
                return

        self.satt_status("Startar tävlingsläge...")
        self.tavling_btn.config(state="disabled")

        def kor():
            try:
                from tavling import starta_tavlingsläge

                starta_tavlingsläge(config)
                spara_config(config)
                self.root.after(0, lambda: self.satt_status("Tävlingsläge avslutat"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel uppstod"))
            finally:
                self.root.after(0, lambda: self.tavling_btn.config(state="normal"))

        threading.Thread(target=kor, daemon=True).start()

    def starta_traning(self):
        """Startar träningsläge i separat tråd"""
        config = ladda_config()

        if config.get("kamera_index") is None:
            messagebox.showerror(
                "Fel", "Välj kamera först! (Inställningar → Välj kamera)"
            )
            return

        if config.get("arduino_port") is None:
            svar = messagebox.askyesno(
                "Varning",
                "Ingen Arduino vald. Vill du fortsätta med manuell start (Enter)?",
            )
            if not svar:
                return

        self.satt_status("Startar träningsläge...")
        self.traning_btn.config(state="disabled")

        def kor():
            try:
                from traning import starta_traningsläge

                starta_traningsläge(config)
                spara_config(config)
                self.root.after(0, lambda: self.satt_status("Träningsläge avslutat"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel uppstod"))
            finally:
                self.root.after(0, lambda: self.traning_btn.config(state="normal"))

        threading.Thread(target=kor, daemon=True).start()

    def starta_analys(self):
        """Startar analysläge i separat tråd"""
        self.satt_status("Startar analysläge...")
        self.analys_btn.config(state="disabled")

        def kor():
            try:
                from analys_main import starta_analysläge

                # Fråga efter videofil
                from tkinter import filedialog

                fil = filedialog.askopenfilename(
                    title="Välj video att analysera",
                    filetypes=[("AVI-filer", "*.avi"), ("Alla filer", "*.*")],
                )

                if fil:
                    starta_analysläge(fil, valt_loppnamn=None, tillåt_nästa_lopp=False)
                    self.root.after(0, lambda: self.satt_status("Analys avslutat"))
                else:
                    self.root.after(0, lambda: self.satt_status("Analys avbruten"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel uppstod"))
            finally:
                self.root.after(0, lambda: self.analys_btn.config(state="normal"))

        threading.Thread(target=kor, daemon=True).start()

    def valj_kamera(self):
        """Öppnar kameravalsdialog"""
        from installningar_meny import andra_kamera

        config = ladda_config()

        self.satt_status("Väljer kamera...")

        def kor():
            try:
                andra_kamera(config)
                self.root.after(0, lambda: self.satt_status("Kamera vald"))
                self.root.after(0, self.uppdatera_status)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel vid kameraval"))

        threading.Thread(target=kor, daemon=True).start()

    def valj_arduino(self):
        """Öppnar Arduino-valdialog"""
        from installningar_meny import andra_arduino

        config = ladda_config()

        self.satt_status("Väljer Arduino...")

        def kor():
            try:
                andra_arduino(config)
                self.root.after(0, lambda: self.satt_status("Arduino vald"))
                self.root.after(0, self.uppdatera_status)
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel vid Arduino-val"))

        threading.Thread(target=kor, daemon=True).start()

    def kalibrera(self):
        """Startar kalibrering"""
        config = ladda_config()

        if config.get("kamera_index") is None:
            messagebox.showerror(
                "Fel", "Välj kamera först! (Inställningar → Välj kamera)"
            )
            return

        self.satt_status("Kalibrerar...")
        self.kalibrera_btn.config(state="disabled")

        def kor():
            try:
                from kalibrera_kamera import kör_kalibrering

                kör_kalibrering(config["kamera_index"], config["kamera_fps"])
                self.root.after(0, lambda: self.satt_status("Kalibrering klar"))
            except Exception as e:
                self.root.after(0, lambda: messagebox.showerror("Fel", str(e)))
                self.root.after(0, lambda: self.satt_status("Fel vid kalibrering"))
            finally:
                self.root.after(0, lambda: self.kalibrera_btn.config(state="normal"))

        threading.Thread(target=kor, daemon=True).start()

    def avsluta(self):
        """Stänger programmet"""
        if messagebox.askyesno("Avsluta", "Vill du avsluta JackTime?"):
            fönster = get_fönster()
            if fönster:
                fönster.stäng()
            self.root.quit()
            self.root.destroy()


def main():
    root = tk.Tk()
    app = JackTimeGUI(root)
    root.mainloop()


if __name__ == "__main__":
    main()
