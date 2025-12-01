#!/usr/bin/env python3
import os
import subprocess
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REQUIREMENTS = os.path.join(PROJECT_ROOT, "requirements.txt")
VENV_DIR = os.path.join(PROJECT_ROOT, "venv")


def check_package(package_name):
    """Kontrollera om ett paket är installerat via dpkg (Debian/Ubuntu/Mint)."""
    try:
        subprocess.check_call(
            ["dpkg", "-s", package_name],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        return True
    except subprocess.CalledProcessError:
        return False


def main():
    # 🔍 Kontrollera att python3-venv finns
    if not check_package("python3-venv"):
        print("🚨 Paketet 'python3-venv' saknas. Installera med:")
        print("    sudo apt install python3-venv")
        print("    eller: sudo pacman -S python-virtualenv")
        sys.exit(1)

    # 🔍 Kontrollera att python3-tk finns
    if not check_package("python3-tk"):
        print("⚠️ Paketet 'python3-tk' saknas. GUI-funktioner kan sluta fungera.")
        print("    Installera med: sudo apt install python3-tk")
        print("    eller: sudo pacman -S python3-tk")

    print("📦 Skapar virtuell miljö i:", VENV_DIR)
    subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])

    pip_path = os.path.join(VENV_DIR, "bin", "pip") if os.name != "nt" else os.path.join(
        VENV_DIR, "Scripts", "pip.exe")

    print("📥 Installerar requirements från:", REQUIREMENTS)
    subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
    try:
        subprocess.check_call([pip_path, "install", "-r", REQUIREMENTS])
    except subprocess.CalledProcessError as e:
        print("🚨 Fel vid installation:", e)
        sys.exit(1)

    print("✅ Virtuell miljö klar! Aktivera den med:")
    if os.name == "nt":
        print(f"{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"source {VENV_DIR}/bin/activate")


if __name__ == "__main__":
    main()
