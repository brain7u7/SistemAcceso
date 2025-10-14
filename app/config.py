"""
app/config.py
-------------
Carga y expone la configuración de la aplicación (desde config.json) y
algunos datos del sistema operativo. Se centraliza para evitar duplicación.
"""

from pathlib import Path
import json
import platform

def cargar_config(archivo="config.json"):
    """
    Lee el archivo JSON de configuración que debe residir en el directorio raíz del proyecto.
    Si no existe, se lanza una excepción clara (para no continuar con valores incompletos).
    """
    try:
        return json.loads(Path(archivo).read_text(encoding="utf-8"))
    except FileNotFoundError:
        print(f"Error Crítico: No se encontró el archivo de configuración '{archivo}'.")
        raise

# Configuración global
CONFIG = cargar_config()

# Datos sobre el sistema donde corre (para decidir GPIO real vs simulación)
SO = platform.system()

# Pines GPIO tomados desde config.json (dict con claves pin_a, pin_b, sensor_abierto, sensor_cerrado)
PINS = CONFIG.get('gpio_pins', {})
