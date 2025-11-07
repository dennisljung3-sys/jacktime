#!/bin/bash

# 📁 Automatisk sökväg till projektmappen (mappen ovanför Installation)
PROJEKTMAPP="$(dirname "$(dirname "$(realpath "$0")")")"

# 🖥️ Starta xfce4-terminal på vänstra halvan av skärmen och kör programmet
xfce4-terminal --geometry=80x50+0+0 --title="Hundtävling" --command="bash -c '
cd \"$PROJEKTMAPP\"
source hundenv/bin/activate
python3 main.py
exec bash'"

