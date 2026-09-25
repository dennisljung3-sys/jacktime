# gui_main.py - Huvud-GUI för JackTime med PySimpleGUI

import PySimpleGUI as sg
import threading
import os
import json
from datetime import datetime
from paths import relativ_sökväg
from confighantering import ladda_config, spara_config
from textutils import sanera_filnamn

# --- Konfiguration ---
sg.theme("DarkBlue3")  # Lätt tema som fungerar bra på äldre datorer


# --- Hjälpfunktioner ---
def kör_i_tråd(func, *args, **kwargs):
    """Kör en funktion i en separat tråd så att GUI inte fryser"""
    thread = threading.Thread(target=func, args=args, kwargs=kwargs, daemon=True)
    thread.start()


def uppdatera_status(window, text, färg="lightblue"):
    """Uppdaterar statusfältet"""
    window["-STATUS-"].update(text, text_color=färg)
    window.refresh()


def hämta_tillgängliga_mappar(typ):
    """Hämtar tillgängliga tränings- eller tävlingsmappar"""
    if typ == "träning":
        basmapp = relativ_sökväg("träning")
    else:
        basmapp = relativ_sökväg("resultat")

    if not os.path.exists(basmapp):
        return []

    mappar = [d for d in os.listdir(basmapp) if os.path.isdir(os.path.join(basmapp, d))]
    if typ == "resultat":
        mappar = [d for d in mappar if d != "träning"]
    return sorted(mappar, reverse=True)  # Senaste först


def hämta_lopp_från_mapp(mapp, typ):
    """Hämtar alla lopp från en specifik mapp"""
    if typ == "träning":
        basmapp = relativ_sökväg("träning", mapp)
    else:
        basmapp = relativ_sökväg("resultat", mapp)

    if not os.path.exists(basmapp):
        return []

    alla_filer = os.listdir(basmapp)
    lopp = []
    for f in alla_filer:
        if f.endswith(".json") and not f.endswith("_sammanfattning.json"):
            if "__analys__" not in f and "__frame_tider" not in f:
                lopp.append(os.path.splitext(f)[0])
    return sorted(lopp)


def hämta_videor_från_lopp(mapp, loppnamn, typ):
    """Hämtar alla videor från ett specifikt lopp"""
    if typ == "träning":
        basmapp = relativ_sökväg("träning", mapp)
    else:
        basmapp = relativ_sökväg("resultat", mapp)

    if not os.path.exists(basmapp):
        return []

    # Hitta alla videor som matchar loppnamnet
    alla_filer = os.listdir(basmapp)
    videor = []
    for f in alla_filer:
        if f.endswith(".avi") and loppnamn in f:
            videor.append(f)
    return sorted(videor)


# --- GUI-funktioner ---


def visa_huvudmeny():
    """Huvudmenyn för JackTime"""

    # Ladda config
    config = ladda_config()

    # Skapa layout
    layout = [
        [
            sg.Text(
                "🐾 JackTime",
                font=("Helvetica", 28, "bold"),
                justification="center",
                expand_x=True,
            )
        ],
        [
            sg.Text(
                "Tidtagning för hundkapplöpning",
                font=("Helvetica", 12),
                justification="center",
                expand_x=True,
            )
        ],
        [sg.HorizontalSeparator()],
        # Statusrad
        [
            sg.Text(
                "📷 Kamera: "
                + ("Vald" if config.get("kamera_index") is not None else "Ej vald"),
                key="-KAMERA_STATUS-",
                size=(20, 1),
            ),
            sg.Text(
                "🔌 Arduino: " + (config.get("arduino_port") or "Ej vald"),
                key="-ARDUINO_STATUS-",
                size=(25, 1),
            ),
        ],
        [sg.HorizontalSeparator()],
        # Huvudknappar
        [
            sg.Button(
                "🏁 Tävlingsläge",
                size=(25, 2),
                key="-TAVLING-",
                button_color=("white", "#4CAF50"),
            )
        ],
        [
            sg.Button(
                "🏋️ Träningsläge",
                size=(25, 2),
                key="-TRANING-",
                button_color=("white", "#2196F3"),
            )
        ],
        [
            sg.Button(
                "📊 Analysläge",
                size=(25, 2),
                key="-ANALYS-",
                button_color=("white", "#FF9800"),
            )
        ],
        [sg.HorizontalSeparator()],
        # Inställningsknappar
        [
            sg.Button("📷 Välj Kamera", size=(15, 1), key="-KAMERA-"),
            sg.Button("🔌 Välj Arduino", size=(15, 1), key="-ARDUINO-"),
            sg.Button("⚡ Kalibrera", size=(15, 1), key="-KALIBRERA-"),
        ],
        [
            sg.Button("📋 Startlistor", size=(15, 1), key="-STARTLISTOR-"),
            sg.Button("📊 Visa Resultat", size=(15, 1), key="-RESULTAT-"),
            sg.Button("⚙️ Inställningar", size=(15, 1), key="-INSTALLNINGAR-"),
        ],
        [sg.HorizontalSeparator()],
        [
            sg.Button(
                "🚪 Avsluta",
                size=(15, 1),
                button_color=("white", "#f44336"),
                key="-AVSLUTA-",
            )
        ],
        # Statusfält längst ner
        [
            sg.Text(
                "🟢 Redo",
                key="-STATUS-",
                text_color="lightgreen",
                size=(50, 1),
                font=("Helvetica", 10),
            )
        ],
    ]

    # Skapa fönster
    window = sg.Window(
        "JackTime - Tidtagning för hundkapplöpning",
        layout,
        finalize=True,
        resizable=False,
        element_justification="center",
    )

    # Huvudloop
    while True:
        event, values = window.read(timeout=100)

        if event == sg.WIN_CLOSED or event == "-AVSLUTA-":
            break

        elif event == "-TAVLING-":
            uppdatera_status(window, "🏁 Startar tävlingsläge...", "yellow")
            from tavling import starta_tavlingsläge

            kör_i_tråd(starta_tavlingsläge, config)
            uppdatera_status(window, "✅ Tävlingsläge startat", "lightgreen")

        elif event == "-TRANING-":
            uppdatera_status(window, "🏋️ Startar träningsläge...", "yellow")
            from traning import starta_traningsläge

            kör_i_tråd(starta_traningsläge, config)
            uppdatera_status(window, "✅ Träningsläge startat", "lightgreen")

        elif event == "-ANALYS-":
            visa_analys_dialog(window)

        elif event == "-KAMERA-":
            visa_kamera_dialog(window)

        elif event == "-ARDUINO-":
            visa_arduino_dialog(window)

        elif event == "-KALIBRERA-":
            uppdatera_status(window, "⚡ Startar kalibrering...", "yellow")
            from kalibrera_kamera import kör_kalibrering

            kör_i_tråd(
                kör_kalibrering, config.get("kamera_index"), config.get("kamera_fps")
            )
            uppdatera_status(window, "✅ Kalibrering klar", "lightgreen")

        elif event == "-STARTLISTOR-":
            visa_startlista_dialog(window)

        elif event == "-RESULTAT-":
            visa_resultat_dialog(window)

        elif event == "-INSTALLNINGAR-":
            visa_installningar_dialog(window)

        # Uppdatera status varje sekund
        if event == sg.TIMEOUT_KEY:
            # Uppdatera config om den ändrats
            config = ladda_config()
            window["-KAMERA_STATUS-"].update(
                "📷 Kamera: "
                + ("Vald" if config.get("kamera_index") is not None else "Ej vald")
            )
            window["-ARDUINO_STATUS-"].update(
                "🔌 Arduino: " + (config.get("arduino_port") or "Ej vald")
            )

    window.close()


# --- Dialoger ---


def visa_analys_dialog(window):
    """Dialog för att välja vad som ska analyseras"""

    # Hämta tillgängliga mappar
    träningsmappar = hämta_tillgängliga_mappar("träning")
    tävlingsmappar = hämta_tillgängliga_mappar("resultat")

    layout = [
        [sg.Text("📊 Analysera", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Välj typ:")],
        [
            sg.Radio("Träning", "ANALYS_TYP", key="-TRÄNING-", default=True),
            sg.Radio("Tävling", "ANALYS_TYP", key="-TAVLING-"),
        ],
        [sg.Text("Välj datum/pass:")],
        [sg.Combo(träningsmappar, key="-MAPP-", size=(30, 1), enable_events=True)],
        [sg.Text("Välj lopp:")],
        [sg.Combo([], key="-LOPP-", size=(30, 1), enable_events=True)],
        [sg.Text("Välj video:")],
        [sg.Combo([], key="-VIDEO-", size=(30, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.Button(
                "📊 Analysera", key="-ANALYSERA-", button_color=("white", "#FF9800")
            ),
            sg.Button("Avbryt", key="-AVBRYT-"),
        ],
    ]

    dialog = sg.Window("Analysera", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-AVBRYT-"):
            break

        # Uppdatera lopp-lista när mapp väljs
        if event == "-MAPP-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]
            if mapp:
                lopp = hämta_lopp_från_mapp(mapp, typ)
                dialog["-LOPP-"].update(values=lopp)
                dialog["-VIDEO-"].update(values=[])

        # Uppdatera video-lista när lopp väljs
        if event == "-LOPP-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]
            lopp = values["-LOPP-"]
            if mapp and lopp:
                videor = hämta_videor_från_lopp(mapp, lopp, typ)
                dialog["-VIDEO-"].update(values=videor)

        if event == "-ANALYSERA-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]
            lopp = values["-LOPP-"]
            video = values["-VIDEO-"]

            if not mapp or not lopp or not video:
                sg.popup_error("Välj mapp, lopp och video först!")
                continue

            dialog.close()
            uppdatera_status(window, f"📊 Analyserar {lopp}...", "yellow")

            from analys_main import starta_analysläge

            video_sökväg = relativ_sökväg(typ, mapp, video)
            kör_i_tråd(starta_analysläge, video_sökväg, None, False)

            uppdatera_status(window, "✅ Analys klar", "lightgreen")
            break

    dialog.close()


def visa_kamera_dialog(window):
    """Dialog för att välja kamera"""
    import cv2

    # Sök efter kameror
    tillgängliga = []
    for i in range(10):
        try:
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                fps = cap.get(cv2.CAP_PROP_FPS)
                tillgängliga.append(f"Index {i} - {w}x{h} @ {int(fps)} FPS")
                cap.release()
        except:
            pass

    if not tillgängliga:
        sg.popup_error("❌ Inga kameror hittades!")
        return

    layout = [
        [sg.Text("📷 Välj kamera", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Tillgängliga kameror:")],
        [
            sg.Listbox(
                tillgängliga, size=(40, 5), key="-KAMERA_LIST-", enable_events=True
            )
        ],
        [sg.Text("Välj FPS:")],
        [sg.Combo([30, 60, 100, 120], default_value=60, key="-FPS-")],
        [sg.HorizontalSeparator()],
        [
            sg.Button("✅ Välj", key="-VALJ-", button_color=("white", "#4CAF50")),
            sg.Button("Avbryt", key="-AVBRYT-"),
        ],
    ]

    dialog = sg.Window("Välj kamera", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-AVBRYT-"):
            break

        if event == "-VALJ-":
            if not values["-KAMERA_LIST-"]:
                sg.popup_error("Välj en kamera först!")
                continue

            # Extrahera index från vald sträng
            vald = values["-KAMERA_LIST-"][0]
            index = int(vald.split("Index ")[1].split(" -")[0])
            fps = values["-FPS-"]

            config = ladda_config()
            config["kamera_index"] = index
            config["kamera_fps"] = fps
            spara_config(config)

            sg.popup(f"✅ Kamera {index} vald med {fps} FPS")
            dialog.close()
            uppdatera_status(window, f"📷 Kamera {index} vald", "lightgreen")
            break

    dialog.close()


def visa_arduino_dialog(window):
    """Dialog för att välja Arduino-port"""
    import serial.tools.list_ports

    portar = list(serial.tools.list_ports.comports())
    if not portar:
        sg.popup_error("❌ Inga portar hittades!")
        return

    port_lista = [f"{p.device} - {p.description}" for p in portar]

    layout = [
        [sg.Text("🔌 Välj Arduino-port", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Tillgängliga portar:")],
        [sg.Listbox(port_lista, size=(40, 5), key="-PORT-")],
        [sg.HorizontalSeparator()],
        [
            sg.Button("✅ Välj", key="-VALJ-", button_color=("white", "#4CAF50")),
            sg.Button("Avbryt", key="-AVBRYT-"),
        ],
    ]

    dialog = sg.Window("Välj Arduino", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-AVBRYT-"):
            break

        if event == "-VALJ-":
            if not values["-PORT-"]:
                sg.popup_error("Välj en port först!")
                continue

            vald = values["-PORT-"][0]
            port = vald.split(" -")[0]

            config = ladda_config()
            config["arduino_port"] = port
            spara_config(config)

            sg.popup(f"✅ Arduino vald på {port}")
            dialog.close()
            uppdatera_status(window, f"🔌 Arduino på {port}", "lightgreen")
            break

    dialog.close()


def visa_startlista_dialog(window):
    """Dialog för att hantera startlistor"""

    layout = [
        [sg.Text("📋 Startlistor", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Button("📝 Skapa ny startlista", key="-SKAPA-", size=(25, 1))],
        [sg.Button("✏️ Redigera startlista", key="-REDIGERA-", size=(25, 1))],
        [sg.Button("📋 Visa startlistor", key="-VISA-", size=(25, 1))],
        [sg.HorizontalSeparator()],
        [sg.Button("Stäng", key="-STANG-")],
    ]

    dialog = sg.Window("Startlistor", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-STANG-"):
            break

        if event == "-SKAPA-":
            dialog.close()
            uppdatera_status(window, "📝 Skapar startlista...", "yellow")
            from startlista import skapa_startlista

            kör_i_tråd(skapa_startlista)
            uppdatera_status(window, "✅ Startlista skapad", "lightgreen")
            break

        if event == "-REDIGERA-":
            dialog.close()
            uppdatera_status(window, "✏️ Redigerar startlista...", "yellow")
            from redigera_startlista import redigera_startlista

            kör_i_tråd(redigera_startlista)
            uppdatera_status(window, "✅ Startlista redigerad", "lightgreen")
            break

        if event == "-VISA-":
            visa_tillgängliga_startlistor(window)

    dialog.close()


def visa_tillgängliga_startlistor(window):
    """Visa tillgängliga startlistor"""
    startlistor_mapp = relativ_sökväg("startlistor")
    if not os.path.exists(startlistor_mapp):
        sg.popup("❌ Inga startlistor hittades!")
        return

    filer = [f for f in os.listdir(startlistor_mapp) if f.endswith(".json")]
    if not filer:
        sg.popup("❌ Inga startlistor hittades!")
        return

    layout = [
        [sg.Text("📋 Tillgängliga startlistor", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Listbox(filer, size=(40, 10), key="-FILER-", enable_events=True)],
        [sg.Multiline("", size=(50, 5), key="-INNEHALL-", disabled=True)],
        [sg.HorizontalSeparator()],
        [sg.Button("Stäng", key="-STANG-")],
    ]

    dialog = sg.Window("Startlistor", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-STANG-"):
            break

        if event == "-FILER-":
            if values["-FILER-"]:
                fil = values["-FILER-"][0]
                sökväg = os.path.join(startlistor_mapp, fil)
                try:
                    with open(sökväg, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    # Visa första 5 loppen
                    text = f"📁 {fil}\n\n"
                    for i, lopp in enumerate(data[:5], 1):
                        text += f"Lopp {i}: {lopp.get('lopp_namn', 'Okänt')}\n"
                        text += f"  Distans: {lopp.get('distans', '?')} m\n"
                        text += f"  Hundar: {len(lopp.get('hundar', {}))} st\n\n"
                    if len(data) > 5:
                        text += f"... och {len(data) - 5} fler lopp"
                    dialog["-INNEHALL-"].update(text)
                except:
                    dialog["-INNEHALL-"].update("❌ Kunde inte läsa filen")

    dialog.close()


def visa_resultat_dialog(window):
    """Dialog för att visa resultat och sammanfattningar"""

    layout = [
        [sg.Text("📊 Resultat och sammanfattningar", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text("Välj typ:")],
        [
            sg.Radio("Träning", "RESULTAT_TYP", key="-TRÄNING-", default=True),
            sg.Radio("Tävling", "RESULTAT_TYP", key="-TAVLING-"),
        ],
        [sg.Text("Välj datum/pass:")],
        [sg.Combo([], key="-MAPP-", size=(30, 1), enable_events=True)],
        [sg.Text("Välj lopp:")],
        [sg.Combo([], key="-LOPP-", size=(30, 1))],
        [sg.HorizontalSeparator()],
        [
            sg.Button(
                "📊 Visa sammanfattning",
                key="-VISA-",
                button_color=("white", "#2196F3"),
            ),
            sg.Button(
                "📤 Exportera till Excel",
                key="-EXPORTERA-",
                button_color=("white", "#4CAF50"),
            ),
            sg.Button("Stäng", key="-STANG-"),
        ],
    ]

    dialog = sg.Window("Resultat", layout, modal=True, finalize=True)

    # Uppdatera mappar initialt
    uppdatera_resultat_mappar(dialog)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-STANG-"):
            break

        if event == "-TRÄNING-" or event == "-TAVLING-":
            uppdatera_resultat_mappar(dialog)

        if event == "-MAPP-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]
            if mapp:
                lopp = hämta_lopp_från_mapp(mapp, typ)
                dialog["-LOPP-"].update(values=lopp)

        if event == "-VISA-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]
            lopp = values["-LOPP-"]

            if not mapp or not lopp:
                sg.popup_error("Välj mapp och lopp först!")
                continue

            dialog.close()
            uppdatera_status(window, f"📊 Visar sammanfattning för {lopp}...", "yellow")

            from sammanfattning import visa_tidigare_sammanfattning

            är_träning = typ == "träning"
            kör_i_tråd(visa_tidigare_sammanfattning, mapp, lopp, None, är_träning)

            uppdatera_status(window, "✅ Sammanfattning visad", "lightgreen")
            break

        if event == "-EXPORTERA-":
            typ = "träning" if values["-TRÄNING-"] else "resultat"
            mapp = values["-MAPP-"]

            if not mapp:
                sg.popup_error("Välj en mapp först!")
                continue

            dialog.close()
            uppdatera_status(window, f"📤 Exporterar {mapp}...", "yellow")

            from sammanfattning import exportera_hel_tävling

            kör_i_tråd(exportera_hel_tävling, mapp)

            uppdatera_status(window, "✅ Export klar", "lightgreen")
            break

    dialog.close()


def uppdatera_resultat_mappar(window):
    """Uppdaterar listan över tillgängliga mappar i resultatdialogen"""
    # Vi behöver veta vilken typ som är vald
    # Detta är en förenkling - i verkligheten skulle vi behöva hämta från dialogens values
    träningsmappar = hämta_tillgängliga_mappar("träning")
    tävlingsmappar = hämta_tillgängliga_mappar("resultat")

    # Uppdatera med båda, men låt användaren välja
    alla_mappar = sorted(set(träningsmappar + tävlingsmappar), reverse=True)
    window["-MAPP-"].update(values=alla_mappar)


def visa_installningar_dialog(window):
    """Dialog för inställningar"""

    config = ladda_config()

    layout = [
        [sg.Text("⚙️ Inställningar", font=("Helvetica", 16, "bold"))],
        [sg.HorizontalSeparator()],
        [sg.Text(f"📷 Kamera: Index {config.get('kamera_index', 'Ej vald')}")],
        [sg.Text(f"🎞️ FPS: {config.get('kamera_fps', 'Ej vald')}")],
        [sg.Text(f"🔌 Arduino: {config.get('arduino_port', 'Ej vald')}")],
        [sg.Text(f"📍 Mållinje: {config.get('mållinje_x', 'Ej satt')}")],
        [sg.HorizontalSeparator()],
        [
            sg.Button("📷 Välj kamera", key="-KAMERA-"),
            sg.Button("🔌 Välj Arduino", key="-ARDUINO-"),
            sg.Button("📍 Sätt mållinje", key="-MALLINJE-"),
        ],
        [sg.Button("⚡ Kalibrera", key="-KALIBRERA-")],
        [sg.HorizontalSeparator()],
        [sg.Button("Stäng", key="-STANG-")],
    ]

    dialog = sg.Window("Inställningar", layout, modal=True, finalize=True)

    while True:
        event, values = dialog.read()

        if event in (sg.WIN_CLOSED, "-STANG-"):
            break

        if event == "-KAMERA-":
            dialog.close()
            visa_kamera_dialog(window)
            break

        if event == "-ARDUINO-":
            dialog.close()
            visa_arduino_dialog(window)
            break

        if event == "-MALLINJE-":
            dialog.close()
            uppdatera_status(window, "📍 Sätter mållinje...", "yellow")
            from installningar_meny import sätt_mållinje

            kör_i_tråd(sätt_mållinje, ladda_config())
            uppdatera_status(window, "✅ Mållinje satt", "lightgreen")
            break

        if event == "-KALIBRERA-":
            dialog.close()
            uppdatera_status(window, "⚡ Startar kalibrering...", "yellow")
            from kalibrera_kamera import kör_kalibrering

            kör_i_tråd(
                kör_kalibrering, config.get("kamera_index"), config.get("kamera_fps")
            )
            uppdatera_status(window, "✅ Kalibrering klar", "lightgreen")
            break

    dialog.close()


# --- Huvudprogram ---


def main():
    """Startar GUI-versionen av JackTime"""
    print("🐾 Startar JackTime GUI...")

    # Skapa nödvändiga mappar
    nödvändiga_mappar = ["resultat", "startlistor", "träning", "data", "logs"]
    for mapp in nödvändiga_mappar:
        os.makedirs(mapp, exist_ok=True)

    # Starta huvudmenyn
    visa_huvudmeny()


if __name__ == "__main__":
    main()
