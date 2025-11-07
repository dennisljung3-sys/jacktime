import cv2
import threading
import platform

from textutils import sanera_filnamn

# Globalt inspelningsobjekt
_inspelningsobjekt = {
    "capture": None,
    "writer": None,
    "aktiv": False,
    "tråd": None
}

def start_inspelning(kamera_index, filnamn, fps=30, upplösning=(1280, 720)):
    """
    Startar videoinspelning från vald kamera till angiven fil.
    Körs i separat tråd.
    """
    filnamn = sanera_filnamn(filnamn)
    
    if _inspelningsobjekt["aktiv"]:
        print("⚠️ Inspelning redan aktiv.")
        return

    if platform.system() == "Windows":
        cap = cv2.VideoCapture(kamera_index, cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(kamera_index)
    if not cap.isOpened():
        print(f"❌ Kunde inte öppna kamera {kamera_index}.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, upplösning[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, upplösning[1])
    cap.set(cv2.CAP_PROP_FPS, fps)

    # Välj codec – H.264 om möjligt, annars MJPEG
    fourcc = cv2.VideoWriter_fourcc(*'avc1')  # H.264
    writer = cv2.VideoWriter(filnamn, fourcc, fps, upplösning)
    if not writer.isOpened():
        print("⚠️ H.264 misslyckades – försöker MJPEG.")
        fourcc = cv2.VideoWriter_fourcc(*'MJPG')
        writer = cv2.VideoWriter(filnamn, fourcc, fps, upplösning)

    if not writer.isOpened():
        print("❌ Kunde inte skapa videofil.")
        cap.release()
        return

    _inspelningsobjekt["capture"] = cap
    _inspelningsobjekt["writer"] = writer
    _inspelningsobjekt["aktiv"] = True

    def inspelningsloop():
        while _inspelningsobjekt["aktiv"]:
            ret, frame = cap.read()
            if ret:
                writer.write(frame)

    tråd = threading.Thread(target=inspelningsloop)
    tråd.start()
    _inspelningsobjekt["tråd"] = tråd
    print(f"📹 Inspelning startad: {filnamn}")

def stoppa_inspelning():
    """
    Stoppar videoinspelning och frigör resurser.
    """
    if not _inspelningsobjekt["aktiv"]:
        print("⚠️ Ingen inspelning att stoppa.")
        return

    _inspelningsobjekt["aktiv"] = False
    _inspelningsobjekt["tråd"].join()

    _inspelningsobjekt["capture"].release()
    _inspelningsobjekt["writer"].release()

    _inspelningsobjekt["capture"] = None
    _inspelningsobjekt["writer"] = None
    _inspelningsobjekt["tråd"] = None

    print("🛑 Inspelning stoppad.")
