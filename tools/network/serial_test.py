#!/usr/bin/env python3
import sys
import serial

if len(sys.argv) < 2:
    print("Använd: python3 serial_test.py /dev/ttyUSB0")
    exit(1)

port = sys.argv[1]

print(f"[INFO] Öppnar {port}...")

ser = serial.Serial(port, 9600, timeout=0.1)

print("[INFO] Läser från Arduino. Tryck Ctrl+C för att avsluta.\n")

try:
    while True:
        line = ser.readline().decode("utf-8").strip()
        if line:
            print(f"[ARDUINO] {line}")
except KeyboardInterrupt:
    print("\nAvslutar.")
