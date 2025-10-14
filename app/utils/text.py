"""
app/utils/text.py
-----------------
Pequeñas utilidades de texto comunes. En este proyecto, usamos norm()
para comparar strings sin que afecten tildes o mayúsculas.
"""

import unicodedata

def norm(texto: str) -> str:
    """
    Normaliza: quita tildes (NFD), deja solo caracteres base (sin diacríticos),
    pasa a minúsculas y recorta espacios.
    Útil para comparar 'Válida' == 'valida', etc.
    """
    if not texto:
        return ""
    txt = unicodedata.normalize("NFD", texto)
    txt = "".join(c for c in txt if unicodedata.category(c) != "Mn")
    return txt.lower().strip()
