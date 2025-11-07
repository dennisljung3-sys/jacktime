import os
from meny import huvudmeny

# Lista över alla viktiga mappar
nödvändiga_mappar = [
    "resultat",
    "startlistor",
    "träning",
    "data"
]

# Skapa dem om de inte finns
for mapp in nödvändiga_mappar:
    os.makedirs(mapp, exist_ok=True)

if __name__ == "__main__":
    huvudmeny()
