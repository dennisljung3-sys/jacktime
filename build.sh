#!/bin/bash
# build.sh - Bygg JackTime till körbar fil

echo "🏗️ Bygger JackTime..."
echo "================================"

# Färger för output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Städa gammalt bygge
echo -e "${YELLOW}🧹 Städar gammalt bygge...${NC}"
rm -rf build dist

# Skapa nödvändiga mappar
echo -e "${YELLOW}📁 Skapar nödvändiga mappar...${NC}"
mkdir -p startlistor data träning resultat logs

# Bygg med PyInstaller
echo -e "${YELLOW}🔨 Bygger programmet...${NC}"
pyinstaller --name "JackTime" \
  --add-data "startlistor:startlistor" \
  --add-data "data:data" \
  --add-data "träning:träning" \
  --add-data "resultat:resultat" \
  --add-data "tools:tools" \
  --hidden-import cv2 \
  --hidden-import serial \
  --hidden-import pandas \
  --hidden-import openpyxl \
  --hidden-import numpy \
  --collect-all cv2 \
  main.py

if [ $? -eq 0 ]; then
  echo -e "${GREEN}✅ Bygge lyckades!${NC}"
else
  echo -e "${RED}❌ Bygge misslyckades!${NC}"
  exit 1
fi

# Skapa en README-fil för användare
cat >dist/JackTime/LAS_MIG.txt <<'EOF'
================================
JACKTIME - Tidtagning för hundkapplöpning
================================

KÖRA PROGRAMMET:
1. Öppna en terminal i denna mapp
2. Skriv: ./JackTime
3. Tryck Enter

VIKTIGT FÖR ARDUINO:
Om du får problem med Arduino-anslutning:
1. Öppna terminal
2. Skriv: sudo usermod -a -G dialout $USER
3. Logga ut och in igen

FILER SOM SKAPAS:
- startlistor/     ← Dina startlistor sparas här
- data/            ← Inställningar sparas här  
- träning/         ← Träningsvideor sparas här
- resultat/        ← Tävlingsvideor sparas här
- logs/            ← Fel-loggar sparas här

Allt sparas i denna mapp - perfekt för USB-minne!
================================
EOF

# Skapa ett enkelt startskript
cat >dist/JackTime/starta_jacktime.sh <<'EOF'
#!/bin/bash
cd "$(dirname "$0")"
./JackTime
EOF
chmod +x dist/JackTime/starta_jacktime.sh

# Skapa loggmapp i dist
mkdir -p dist/JackTime/logs

echo -e "${GREEN}📁 Programmet finns i: dist/JackTime/${NC}"
echo -e "${GREEN}📦 Storlek: $(du -sh dist/JackTime/ | cut -f1)${NC}"
echo ""
echo -e "${YELLOW}För att testa:${NC}"
echo "  cd dist/JackTime/"
echo "  ./JackTime"
echo ""
echo -e "${YELLOW}För att distribuera på USB:${NC}"
echo "  cp -r dist/JackTime/ /media/ditt_usb_minne/"
