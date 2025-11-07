import serial.tools.list_ports

def välj_arduino_port():
    """
    Söker efter tillgängliga COM-portar och låter användaren välja.
    Bekräftar att en Arduino är ansluten genom att försöka öppna porten.
    Returnerar vald portsträng, t.ex. 'COM3'.
    """

    portar = list(serial.tools.list_ports.comports())
    if not portar:
        print("❌ Inga portar hittades.")
        return None

    print(f"🔍 {len(portar)} portar hittades.")
    for i, port in enumerate(portar):
        print(f"{i}: {port.device}")

    while True:
        try:
            val = int(input("👉 Ange numret för önskad port: "))
            if 0 <= val < len(portar):
                vald_port = portar[val].device
                print(f"✅ Arduino hittades på {vald_port}. Använd denna? (J/N): ", end="")
                svar = input().strip().lower()
                if svar == "j":
                    # Testa att öppna porten
                    try:
                        ser = serial.Serial(vald_port, 9600, timeout=1)
                        ser.close()
                        print(f"🔌 Ansluten till Arduino på {vald_port}")
                        return vald_port
                    except serial.SerialException:
                        print("⚠️ Kunde inte öppna porten. Välj en annan.")
                else:
                    print("🔁 Välj en annan port.")
            else:
                print("⚠️ Ogiltigt val. Försök igen.")
        except ValueError:
            print("⚠️ Ange ett heltal.")
