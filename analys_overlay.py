import cv2

def rita_overlay(frame, mållinje_x=None, tid_str=None):
    """
    Ritar mållinje och instruktioner på videoframe.
    """
    höjd, bredd = frame.shape[:2]
    x = bredd // 2 if mållinje_x is None else int(mållinje_x)

    # Röd mållinje
    cv2.line(frame, (x, 0), (x, höjd), (0, 0, 255), 2)

    # Tidtext
    if tid_str:
        cv2.putText(frame, tid_str, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (255, 255, 255), 2)

    # Instruktioner
    instruktion = "A/D = BACKA/FRAM, 1-6 = VAL AV HUND, Q = AVSLUTA"
    fontstorlek = max(0.5, min(1.2, höjd / 600))
    cv2.putText(frame, instruktion, (10, höjd - 20), cv2.FONT_HERSHEY_SIMPLEX, fontstorlek, (0, 0, 255), 2)

    return frame
