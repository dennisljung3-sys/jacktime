#!/usr/bin/env python3
import socket
import time
import serial
import threading
import os

SERVER_IP = "0.0.0.0"   # Huvuddatorn lyssnar på alla interfaces
SERVER_PORT = 5005
ARDUINO_PORT = "/dev/ttyUSB0"
ARDUINO_BAUD = 9600

# Global variabel för att signalera att Arduino gett "start"
arduino_triggered = False


def read_from_arduino():
    """
    Läser från Arduino tills "start" dyker upp.
    Sätter global variabel arduino_triggered = True
    """
    global arduino_triggered
    print(f"[INFO] Öppnar Arduino på {ARDUINO_PORT}...")

    try:
        ser = serial.Serial(ARDUINO_PORT, ARDUINO_BAUD, timeout=0.1)
    except Exception as e:
        print(f"[FEL] Kunde inte öppna Arduino-porten: {e}")
        return

    print("[INFO] Arduino ansluten, väntar på signal...")

    while True:
        try:
            line = ser.readline().decode("utf-8").strip().lower()
            if line == "start":
                print("[ARDUINO] START mottaget!")
                arduino_triggered = True
        except:
            pass

        time.sleep(0.01)


def send_file(sock):
    """
    Skickar en testfil till splitdatorn.
    Om filen saknas skapas en liten testfil automatiskt.
    """
    filename = "testfile.txt"

    if not os.path.exists(filename):
        with open(filename, "w") as f:
            f.write("Detta är en testfil för filöverföring.\n")

    size = os.path.getsize(filename)
    print(f"[INFO] Skickar {filename} ({size} bytes)")

    # Skicka header
    sock.sendall(f"FILE {filename} {size}\n".encode())

    # Skicka filens innehåll
    with open(filename, "rb") as f:
        data = f.read()
        sock.sendall(data)

    print("[INFO] Fil skickad!\n")


def main():
    global arduino_triggered

    print("[SERVER] Startar...")
    print(f"[INFO] Lyssnar på port {SERVER_PORT}...")
    print("[INFO] Startar Arduino-lyssnare i bakgrunden...\n")

    # Starta separat tråd som lyssnar på Arduino
    threading.Thread(target=read_from_arduino, daemon=True).start()

    # Starta TCP-server
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(1)

    print("[INFO] Väntar på anslutning från splitdatorn...")
    conn, addr = server_sock.accept()
    print(f"[INFO] Splitdator ansluten från {addr}\n")

    while True:
        print("Välj ett alternativ:")
        print("1. Vänta på Arduino och skicka START")
        print("2. Skicka testfil")
        print("3. Avsluta")
        choice = input("> ").strip()

        if choice == "1":
            print("[INFO] Väntar på Arduino signal...")

            # vänta tills Arduino triggar
            while not arduino_triggered:
                time.sleep(0.01)

            # nollställ flagga
            arduino_triggered = False

            # Arduino gav startsignal → skicka START
            t1 = time.time()
            conn.sendall(b"START\n")

            # vänta på ACK
            data = conn.recv(1024).decode().strip()
            t2 = time.time()

            if data.startswith("ACK"):
                client_time = float(data.split()[1])
                rtt = t2 - t1
                ow = rtt / 2

                print("\n=== STARTSIGNAL RESULTAT ===")
                print(f"Roundtrip: {rtt:.6f} sek")
                print(f"One-way (beräknad): {ow:.6f} sek")
                print(f"Client mottog START vid: {client_time}")
                print("===========================\n")
            else:
                print("[FEL] Splitdator skickade inget korrekt ACK.")

        elif choice == "2":
            send_file(conn)

        elif choice == "3":
            print("[INFO] Avslutar server.")
            break

        else:
            print("[FEL] Ogiltigt val.")


if __name__ == "__main__":
    main()
