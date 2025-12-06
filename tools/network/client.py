#!/usr/bin/env python3
"""
client.py (Version 2)
- Kopplas mot server och svarar på kommandon:
  PING, VERSION?, START, UPDATE_BEGIN, FILE <path> <size>, UPDATE_END
- Tar emot filer och skriver dem säkert (tempfile -> rename)
- Sparar version i ~/jacktime/version.txt
- Loggar ut till stdout
"""

import socket
import os
import sys
import time

from protocol import recv_line, send_line, recv_file_to_temp

# Konfiguration
SERVER_IP = "192.168.10.1"   # Ändra till din huvuddators IP om behövligt
SERVER_PORT = 5005

PROJECT_BASE = os.path.expanduser("~/jacktime")
VERSION_FILE = os.path.join(PROJECT_BASE, "version.txt")


def ensure_base():
    os.makedirs(PROJECT_BASE, exist_ok=True)


def write_version(version):
    ensure_base()
    with open(VERSION_FILE, "w") as f:
        f.write(version + "\n")


def handle_file_command(conn, header):
    """
    header = 'FILE rel/path.ext size'
    Läs size bytes och skriv till PROJECT_BASE/rel/path.ext.part -> rename
    """
    try:
        parts = header.split(maxsplit=2)
        if len(parts) != 3:
            send_line(conn, "ERROR bad FILE header")
            return
        _, relpath, size = parts
        size = int(size)
        target = os.path.join(PROJECT_BASE, relpath)
        target_dir = os.path.dirname(target)
        os.makedirs(target_dir, exist_ok=True)
        print(f"[FILE] Tar emot {relpath} ({size} bytes)...")
        recv_file_to_temp(conn, target, size)
        print(f"[FILE] Sparad: {target}")
        send_line(conn, "FILE_RECEIVED")
    except Exception as e:
        print(f"[FILE] Fel: {e}")
        send_line(conn, "ERROR file_receive_failed")


def run_client(server_ip=SERVER_IP, server_port=SERVER_PORT):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    print(f"[CLIENT] Försöker ansluta till {server_ip}:{server_port} ...")
    sock.connect((server_ip, server_port))
    print("[CLIENT] Ansluten. Väntar på kommandon...\n")

    try:
        while True:
            line = recv_line(sock)
            if not line:
                # tom rad eller timeout - fortsätt lyssna
                time.sleep(0.01)
                continue

            # DEBUG
            # print(f"[CLIENT] Kommando: {line}")

            if line == "PING":
                send_line(sock, "PONG")
            elif line == "VERSION?":
                # returnera version (om finns)
                ver = ""
                if os.path.exists(VERSION_FILE):
                    with open(VERSION_FILE, "r") as f:
                        ver = f.read().strip()
                else:
                    ver = "none"
                send_line(sock, f"VERSION {ver}")
            elif line == "START":
                # mottog start -> svara med ACK + lokal timestamp
                t = time.time()
                print(f"[START] Mottog START! ({t})")
                send_line(sock, f"ACK {t}")
            elif line.startswith("UPDATE_BEGIN"):
                # format: UPDATE_BEGIN <version> <filecount>
                parts = line.split(maxsplit=2)
                version = parts[1] if len(parts) > 1 else "unknown"
                filecount = int(parts[2]) if len(parts) > 2 else 0
                print(f"[UPDATE] Börjar update version {
                      version} ({filecount} filer)...")
                # ta emot filer tills UPDATE_END
                received = 0
                while True:
                    header = recv_line(sock)
                    if not header:
                        time.sleep(0.01)
                        continue
                    if header == "UPDATE_END":
                        print("[UPDATE] Färdig med uppdatering.")
                        send_line(sock, "UPDATE_OK")
                        write_version(version)
                        break
                    if header.startswith("FILE "):
                        handle_file_command(sock, header)
                        received += 1
                    else:
                        print(f"[UPDATE] Okänt header: {header}")
            elif line.startswith("FILE "):
                # Direkt fil (t.ex. testfil) - hantera samma som ovan
                handle_file_command(sock, line)
            else:
                print(f"[CLIENT] Okänt kommando: {line}")
    except KeyboardInterrupt:
        print("\n[CLIENT] Avslutar (Ctrl+C).")
    except Exception as e:
        print(f"[CLIENT] Fel: {e}")
    finally:
        try:
            sock.close()
        except:
            pass


if __name__ == "__main__":
    run_client()
