#!/usr/bin/env python3
import socket
import time
import os

SERVER_IP = "192.168.10.1"   # Ange huvuddatorns IP här
SERVER_PORT = 5005


def main():
    print("[CLIENT] Startar...")

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    print(f"[INFO] Ansluter till server {SERVER_IP}:{SERVER_PORT} ...")
    sock.connect((SERVER_IP, SERVER_PORT))
    print("[INFO] Ansluten!\n")

    while True:
        data = sock.recv(1024).decode()

        if not data:
            continue

        data = data.strip()

        # STARTSIGNAL
        if data == "START":
            t = time.time()
            print(f"[INFO] START mottagen! ({t})")
            sock.sendall(f"ACK {t}\n".encode())

        # FILÖVERFÖRING
        elif data.startswith("FILE"):
            _, filename, size = data.split()
            size = int(size)

            print(f"[INFO] Tar emot fil {filename} ({size} bytes)")

            # Läs filinnehåll
            received = 0
            chunks = []

            while received < size:
                chunk = sock.recv(4096)
                if not chunk:
                    break
                chunks.append(chunk)
                received += len(chunk)

            # Spara fil
            with open(filename, "wb") as f:
                for c in chunks:
                    f.write(c)

            print(f"[INFO] Fil {filename} sparad!\n")

        else:
            print(f"[VARNING] Okänt meddelande: {data}")


if __name__ == "__main__":
    main()
