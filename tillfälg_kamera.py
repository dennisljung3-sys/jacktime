import cv2

cap = cv2.VideoCapture(2)  # prova även 1 om 0 inte funkar
if not cap.isOpened():
    print("❌ Kunde inte öppna kameran")
else:
    while True:
        ret, frame = cap.read()
        if not ret:
            print("❌ Ingen bild från kameran")
            break
        cv2.imshow("Testkamera", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

cap.release()
cv2.destroyAllWindows()
