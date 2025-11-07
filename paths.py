import os

# Projektets rotmapp – där main.py ligger
PROJEKTMAPP = os.path.dirname(os.path.abspath(__file__))

def relativ_sökväg(*delar):
    """
    Returnerar en absolut sökväg baserat på projektets rotmapp.
    Exempel: relativ_sökväg("träning", "2025-11-01") → /projektmapp/träning/2025-11-01
    """
    return os.path.join(PROJEKTMAPP, *delar)
