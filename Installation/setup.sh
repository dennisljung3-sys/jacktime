#!/bin/bash

echo "📦 Skapar virtuell miljö..."
python3 -m venv hundenv
source hundenv/bin/activate

echo "📥 Installerar beroenden..."
pip install --upgrade pip
pip install -r requirements.txt

echo "✅ Klar! Kör programmet med:"
echo "source hundenv/bin/activate && python3 main.py"

