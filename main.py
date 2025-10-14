"""
main.py
-------
Punto de entrada de la aplicación.

Responsabilidades:
- Apagar advertencias SSL (porque requests se hace con verify=False por la fuente original).
- Construir las dependencias (BD, JSON store, ControlAcceso, EscanerQR).
- Iniciar el bucle de escaneo HID (input por consola).
- Al salir, limpiar GPIO si aplica.

IMPORTANTE: Ejecutar SIEMPRE desde el directorio del proyecto para que Python
encuentre tus módulos Cifrado.py / Descifrado.py / Clasificador.py en el sys.path.
"""

import urllib3

# Config y componentes del proyecto
from app.config import CONFIG
from app.data.db import BaseDatos
from app.data.json_store import GestorJSON
from app.core.acceso import ControlAcceso
from app.core.escaner import EscanerQR
from app.hardware.gpio_ctrl import cleanup  # Limpia pines al terminar

# Evita warnings por verify=False en requests
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def main():
    # 1) Inicializa capa de datos
    db = BaseDatos(CONFIG['database_file'])
    json_store = GestorJSON(
    CONFIG['json_files']['alumnos_no_inscritos'],
    CONFIG['json_files']['profesores_no_validos'],
    CONFIG['json_files'].get('bloqueados')  # <- nuevo parámetro opcional
)


    # 2) Lógica de negocio (control de acceso)
    acceso = ControlAcceso(db, json_store)

    # 3) Escáner que orquesta el flujo de URL -> verificación BD/scrapeo -> accion
    escaner = EscanerQR(acceso, db)

    try:
        # 4) Inicia bucle de lectura por consola (simulación de lector HID)
        escaner.iniciar()
    finally:
        # 5) Siempre limpia GPIO si estás en Linux/RPi y hubo setup correcto
        cleanup()

if __name__ == "__main__":
    main()

