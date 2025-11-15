import os
import subprocess
import sys

# 🔧 Projektets root-mapp
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# 📦 Sökväg till requirements.txt
REQUIREMENTS = os.path.join(os.path.dirname(__file__), "requirements.txt")

# 📂 Virtuell miljö i projektets root
VENV_DIR = os.path.join(PROJECT_ROOT, "venv")

def main():
    print("📦 Skapar virtuell miljö i:", VENV_DIR)
    subprocess.check_call([sys.executable, "-m", "venv", VENV_DIR])

    # Aktivera pip från den virtuella miljön
    pip_path = os.path.join(VENV_DIR, "bin", "pip") if os.name != "nt" else os.path.join(VENV_DIR, "Scripts", "pip.exe")

    print("📥 Installerar requirements från:", REQUIREMENTS)
    subprocess.check_call([pip_path, "install", "--upgrade", "pip"])
    subprocess.check_call([pip_path, "install", "-r", REQUIREMENTS])

    print("✅ Virtuell miljö klar! Aktivera den med:")
    if os.name == "nt":
        print(f"{VENV_DIR}\\Scripts\\activate")
    else:
        print(f"source {VENV_DIR}/bin/activate")

if __name__ == "__main__":
    main()
