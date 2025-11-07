import cv2
import platform
import tkinter as tk
from textutils import ersätt_svenska_tecken

def hämta_skärmstorlek():
    root = tk.Tk()
    root.withdraw()
    return root.winfo_screenwidth(), root.winfo_screenheight()

def rita_overlay(frame, mållinje_x=None, tid_str=None):
    höjd, bredd = frame.shape[:2]
    x = mållinje_x if mållinje_x is not None else bredd // 2
    cv2.line(frame, (x, 0), (x, höjd), (0, 0, 255), 2)
    if tid_str:
        tid_str = ersätt_svenska_tecken(tid_str)
        cv2.putText(frame, tid_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)
    return frame

def förbered_kamera_och_mållinje(config):
    mållinje_x = None
    if platform.system() == "Windows":
        cap = cv2.VideoCapture(config["kamera_index"], cv2.CAP_DSHOW)
    else:
        cap = cv2.VideoCapture(config["kamera_index"])
    cap.set(cv2.CAP_PROP_FPS, config["kamera_fps"])

    if not cap.isOpened():
        print("❌ Kunde inte öppna kameran.")
        return None, {}

    verifierad_fps = cap.get(cv2.CAP_PROP_FPS)
    config["verifierad_fps"] = verifierad_fps

    höjd = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    bredd = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))

    screen_width, screen_height = hämta_skärmstorlek()
    fönster_bredd = screen_width // 2
    fönster_höjd = screen_height // 2
    x_pos = screen_width // 2
    y_pos = 0

    def sätt_mållinje(event, x, y, flags, param):
        nonlocal mållinje_x
        if event == cv2.EVENT_LBUTTONDOWN:
            mållinje_x = int(x)
            print(f"📍 Ny mållinje satt vid x = {mållinje_x}")

    cv2.namedWindow("Förhandsvisning", cv2.WINDOW_NORMAL)
    cv2.resizeWindow("Förhandsvisning", fönster_bredd, fönster_höjd)
    cv2.moveWindow("Förhandsvisning", x_pos, y_pos)

    callback_satt = False

    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Kunde inte läsa från kameran.")
            break

        if not callback_satt:
            try:
                if cv2.getWindowProperty("Förhandsvisning", cv2.WND_PROP_VISIBLE) >= 1:
                    cv2.setMouseCallback("Förhandsvisning", sätt_mållinje)
                    callback_satt = True
            except cv2.error:
                pass

        visning = rita_overlay(frame, mållinje_x)
        cv2.imshow("Förhandsvisning", visning)
        tangent = cv2.waitKey(1) & 0xFF
        if tangent == ord('a'):
            mållinje_x = max(0, (mållinje_x or bredd // 2) - 10)
        elif tangent == ord('d'):
            mållinje_x = min(bredd, (mållinje_x or bredd // 2) + 10)
        elif tangent == ord('q'):
            break

    if mållinje_x is None:
        mållinje_x = bredd // 2

    cv2.destroyAllWindows()

    metadata = {
        "mållinje_x": mållinje_x,
        "skärmstorlek": (screen_width, screen_height),
        "kamera_index": config["kamera_index"],
        "fps": verifierad_fps
    }

    return cap, metadata

