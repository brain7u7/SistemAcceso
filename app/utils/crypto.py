"""
app/utils/crypto.py
-------------------
"Wrapper" que reusa TUS implementaciones reales de encriptar/desencriptar.
No implementamos nada aquí: solo importamos tus funciones para que el resto
del proyecto las invoque desde una ruta consistente (app.utils.crypto).
"""

# IMPORTANTE:
# - Este import asume que Cifrado.py y Descifrado.py están junto a main.py (raíz).
# - Si mueves esos archivos, actualiza estas rutas.
from Cifrado import encriptar as _enc
from Descifrado import desencriptar as _dec

def encriptar(txt: str) -> str:
    """
    Envoltorio del encriptado. Delega a tu Cifrado.encriptar(...).
    Mantenemos la firma simple porque los modelos/DB esperan un str->str.
    """
    return _enc(txt)

def desencriptar(token: str) -> str:
    """
    Envoltorio del desencriptado. Delega a tu Descifrado.desencriptar(...).
    Igual que arriba: str->str. Si tu función lanza, dejamos que propague.
    """
    return _dec(token)

