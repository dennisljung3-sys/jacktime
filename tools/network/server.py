#!/usr/bin/env python3
"""
server.py (Version 2)
- Menydriven verktyg för:
  1) START-test (Arduino -> client)
  2) Latens-test (manuellt START)
  3) Skicka testfil
  4) Push koduppdatering (auto-update ~/jacktime/)
  5) Kontrollera client version
  6) Ping client
  7) Avsluta
- Använder protocol.py
- Arduino på /dev/ttyUSB0 (du kan välja en annan port i ARDUINO_PORT)
"""

import os
import time
import socket
import threading
import serial
import sys
from datetime import datetime

from protocol import send_line, recv_line, send_file

# Konfiguration
SERVER_IP = "0.0.0.0"
SERVER_PORT = 5005

ARDUINO_PORT = "/dev/ttyUSB0"   # du sa att Arduino dyker upp som /dev/ttyUSB0
ARDUINO_BAUD = 9600

# Vad som ska IGNORERAS vid sync (Alternativ C)
IGNORED_DIRS = {".git", "__pycache__", "videos", "results"}
IGNORED_EXTS = {".pyc", ".log", ".tmp", ".mp4", ".avi", ".mov"}

# Baspath som ska synkas från server -> client
PROJECT_BASE = os.path.expanduser("~/jacktime")

# global flag från Arduino-thread
arduino_triggered = threading.Event()


def arduino_listener(port=ARDUINO_PORT, baud=ARDUINO_BAUD):
    """Tråd som lyssnar på Arduino och sätter arduino_triggered vid 'start'."""
    try:
        ser = serial.Serial(port, baud, timeout=0.1)
    except Exception as e:
        print(f"[ARDUINO] Kunde inte öppna port {port}: {e}")
        return

    print(f"[ARDUINO] Lyssnar på {port} (baud={baud}) ...")
    try:
        while True:
            line = ser.readline().decode(errors="ignore").strip().lower()
            if line == "start":
                print("[ARDUINO] START mottaget från Arduino!")
                arduino_triggered.set()
            time.sleep(0.01)
    except Exception as e:
        print(f"[ARDUINO] Fel i lyssnare: {e}")
    finally:
        try:
            ser.close()
        except:
            pass


def accept_client(server_sock: socket.socket):
    """Acceptera en client-anslutning (blockerar)."""
    print(f"[SERVER] Väntar på client (port {SERVER_PORT})...")
    conn, addr = server_sock.accept()
    print(f"[SERVER] Client ansluten: {addr}")
    return conn, addr


def list_files_to_send(base_path):
    """Går igenom base_path och returnerar list av (relpath, fullpath, size)."""
    files = []
    base_path = os.path.abspath(base_path)
    for root, dirs, filenames in os.walk(base_path):
        # filtrera bort ignorerade mappar
        # modify dirs in-place to prune walk
        dirs[:] = [d for d in dirs if d not in IGNORED_DIRS]
        for fname in filenames:
            if any(fname.endswith(ext) for ext in IGNORED_EXTS):
                continue
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, base_path)
            files.append((rel.replace(os.sep, "/"),
                         full, os.path.getsize(full)))
    return files


def push_update(conn: socket.socket):
    """Push hela projektet (enligt list_files_to_send) till client."""
    version = datetime.utcnow().isoformat(timespec="seconds") + "Z"
    files = list_files_to_send(PROJECT_BASE)
    filecount = len(files)
    print(f"[UPDATE] Version: {version} – {filecount} filer att skicka.")

    send_line(conn, f"UPDATE_BEGIN {version} {filecount}")

    # skicka filer en och en
    for relpath, fullpath, size in files:
        print(f"[UPDATE] Skickar {relpath} ({size} bytes)")
        # header
        send_line(conn, f"FILE {relpath} {size}")
        # body
        send_file(conn, fullpath)
        # signalera att filen slutat (client vet via size)
        # vi väntar på ack per fil (optional) — här väntar vi kort för robusthet
        ack = recv_line(conn, timeout=5)
        if ack != "FILE_RECEIVED":
            print(f"[UPDATE] WARN: förväntade FILE_RECEIVED men fick '{ack}'")
    # avsluta update
    send_line(conn, "UPDATE_END")
    print("[UPDATE] Klar. Väntar på client svar...")
    resp = recv_line(conn, timeout=10)
    print(f"[UPDATE] Client svarade: {resp}")


def send_testfile(conn: socket.socket, filename=None):
    """Skickar en liten testfil (eller vilken fil som helst) till client."""
    if filename is None:
        filename = "testfile.txt"
        with open(filename, "w") as f:
            f.write("Testfil från server - " +
                    datetime.utcnow().isoformat() + "\n")
    size = os.path.getsize(filename)
    print(f"[TESTFILE] Skickar {filename} ({size} B)")
    send_line(conn, f"FILE {os.path.basename(filename)} {size}")
    send_file(conn, filename)
    # vänta på FILE_RECEIVED
    ack = recv_line(conn, timeout=5)
    print(f"[TESTFILE] Client ack: {ack}")


def do_start_via_arduino(conn: socket.socket):
    """Vänta på Arduino och skicka START när Arduino triggar."""
    print("[START] Väntar på Arduino-trigger...")
    arduino_triggered.wait()
    arduino_triggered.clear()
    t1 = time.time()
    send_line(conn, "START")
    # vänta på ACK med timestamp
    line = recv_line(conn, timeout=5)
    t2 = time.time()
    if line and line.startswith("ACK"):
        try:
            _, client_ts = line.split(maxsplit=1)
            client_ts = float(client_ts)
        except Exception:
            client_ts = None
        rtt = t2 - t1
        print("=== STARTRESULTAT ===")
        print(f"Roundtrip: {rtt:.6f} s")
        print(f"One-way est.: {rtt/2:.6f} s")
        if client_ts:
            print(f"Client timestamp: {client_ts} (client localtime)")
        print("=====================")
    else:
        print("[START] Ingen giltig ACK från client.")


def do_manual_start(conn: socket.socket):
    """Skicka START manuellt (används för latens-test)."""
    input("Tryck ENTER för att skicka START (manuellt)...")
    t1 = time.time()
    send_line(conn, "START")
    line = recv_line(conn, timeout=5)
    t2 = time.time()
    if line and line.startswith("ACK"):
        try:
            _, client_ts = line.split(maxsplit=1)
            client_ts = float(client_ts)
        except:
            client_ts = None
        rtt = t2 - t1
        print("=== MANUELL START RESULTAT ===")
        print(f"Roundtrip: {rtt:.6f} s")
        print(f"One-way est.: {rtt/2:.6f} s")
        if client_ts:
            print(f"Client timestamp: {client_ts}")
        print("================================")
    else:
        print("[MANUAL] Ingen eller ogiltig ACK.")


def do_ping(conn: socket.socket):
    send_line(conn, "PING")
    resp = recv_line(conn, timeout=3)
    print(f"[PING] Svar: {resp}")


def check_version(conn: socket.socket):
    send_line(conn, "VERSION?")
    resp = recv_line(conn, timeout=3)
    print(f"[VERSION] Client svar: {resp}")


def main_menu(conn: socket.socket):
    while True:
        print("\n==========================")
        print("   NETWORK/UPDATE MENU")
        print("==========================")
        print("1. Testa START-signal (Arduino -> client)")
        print("2. Mät latens (manuellt START)")
        print("3. Skicka testfil")
        print("4. Push koduppdatering (Auto-Update)")
        print("5. Kontrollera splitdatorns version")
        print("6. Ping splitdator")
        print("7. Avsluta")
        choice = input("> ").strip()

        if choice == "1":
            do_start_via_arduino(conn)
        elif choice == "2":
            do_manual_start(conn)
        elif choice == "3":
            send_testfile(conn)
        elif choice == "4":
            push_update(conn)
        elif choice == "5":
            check_version(conn)
        elif choice == "6":
            do_ping(conn)
        elif choice == "7":
            print("[SERVER] Avslutar menu.")
            break
        else:
            print("Ogiltigt val.")


def main():
    # starta Arduino-lyssnaren i bakgrunden
    t = threading.Thread(target=arduino_listener, daemon=True)
    t.start()

    # starta server socket
    server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server_sock.bind((SERVER_IP, SERVER_PORT))
    server_sock.listen(1)

    conn, addr = accept_client(server_sock)
    try:
        main_menu(conn)
    except KeyboardInterrupt:
        print("\n[SERVER] Avbruten med Ctrl+C")
    finally:
        try:
            conn.close()
        except:
            pass
        server_sock.close()
        print("[SERVER] Stoppad.")


if __name__ == "__main__":
    main()
