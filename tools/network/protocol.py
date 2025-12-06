#!/usr/bin/env python3
"""
protocol.py
- Hjälp-funktioner för text/binary protokoll mellan server och client.
- Använder '\n' som radseparator för kommandon.
- Funkar bra över TCP sockets.
"""

import os
import socket

LINESEP = b'\n'


def send_line(sock: socket.socket, line: str):
    """Skicka en rad (text) och avsluta med newline."""
    if not line.endswith("\n"):
        line = line + "\n"
    sock.sendall(line.encode("utf-8"))


def recv_line(sock: socket.socket, timeout=None) -> str:
    """
    Läs en rad tills newline. Returnerar str utan newline.
    Blockerar tills newline eller socket stängs.
    """
    buffer = bytearray()
    sock.settimeout(timeout)
    try:
        while True:
            ch = sock.recv(1)
            if not ch:
                break  # connection closed
            if ch == LINESEP:
                break
            buffer.extend(ch)
    except socket.timeout:
        return ""
    finally:
        sock.settimeout(None)
    return buffer.decode("utf-8", errors="replace").strip()


def send_file(sock: socket.socket, local_path: str):
    """
    Skicka filen på local_path. Preface: caller must send header
    e.g. send_line(sock, f"FILE {relpath} {size}")
    Then call send_file to stream bytes exactly.
    """
    with open(local_path, "rb") as f:
        while True:
            chunk = f.read(4096)
            if not chunk:
                break
            sock.sendall(chunk)


def recv_exact(sock: socket.socket, size: int) -> bytes:
    """Läs exakt size bytes eller raise ConnectionError."""
    parts = []
    remaining = size
    while remaining > 0:
        chunk = sock.recv(min(4096, remaining))
        if not chunk:
            raise ConnectionError(
                "Connection closed while receiving file data")
        parts.append(chunk)
        remaining -= len(chunk)
    return b"".join(parts)


def recv_file_to_temp(sock: socket.socket, target_path: str, size: int):
    """
    Ta emot size bytes från socket och skriv till en temporär fil.
    Efter färdig mottagning byts temp -> target atomärt.
    """
    tmp = target_path + ".part"
    os.makedirs(os.path.dirname(target_path), exist_ok=True)
    with open(tmp, "wb") as f:
        remaining = size
        while remaining > 0:
            chunk = sock.recv(min(4096, remaining))
            if not chunk:
                raise ConnectionError("Connection closed while receiving file")
            f.write(chunk)
            remaining -= len(chunk)
    # rename atomiskt
    os.replace(tmp, target_path)
