"""
app/core/acceso.py
------------------
Contiene la clase ControlAcceso, que encapsula:
- La lógica de abrir/cerrar cerradura (GPIO real o simulación).
- Actualización del estado de bicicleta en BD (entrada/salida).
- Registro de nuevos usuarios (alumno/profesor) con decisión de almacenar en BD o JSON.

Flujo de alto nivel:
- Si el usuario YA existe, solo se decide ENTRADA/SALIDA y se actualiza en BD.
- Si NO existe, se hace scraping, se determina 'estado' y se decide:
  - Alumno Inscrito -> insertar en BD con acción y estado de bici.
  - Profesor Válida -> insertar en BD con acción y estado de bici.
  - Caso contrario -> guardar en JSON de "no inscrito" o "no válido".
"""

import time, datetime, getpass
from app.utils.crypto import encriptar
from app.hardware.gpio_ctrl import leer_estado_actuador, energizar, desenergizar, GPIO_OK
from app.utils.text import norm
from app.config import CONFIG


class ControlAcceso:
    # Contadores globales de entradas/salidas
    contador_ent = 0
    contador_sal = 0

    def __init__(self, db, json_store):
        self.db = db
        self.json = json_store
        self.intentos_no_inscritos = {}
        # Lee desde config.json (antes estaba “3” fijo)
        self.limite_intentos = CONFIG.get("limite_intentos", 3)

    # ---------- GPIO: helper de confirmación por sensores ----------
    def _esperar_movimiento_objetivo(self, estado_objetivo: str, timeout: float = 8.0) -> bool:
        """
        Espera (hasta timeout) a que 'leer_estado_actuador()' coincida con el estado deseado.
        Devuelve True si se confirmó el movimiento; False si hubo timeout o error.
        """
        inicio = time.time()
        while time.time() - inicio < timeout:
            if leer_estado_actuador() == estado_objetivo:
                return True
            time.sleep(0.05)
        return False

    # ---------- Accionamiento de cerradura ----------
    def abrir_cerradura(self, identificador: str, tipo: str) -> str:
        """
        Decide 'entrada' (guardar) o 'salida' (sacar) en base al flag 'tiene_bici_guardada' en BD.
        - En simulación (Windows): solo alterna el flag en BD y retorna acción.
        - En GPIO real (Linux/RPi): energiza pines, espera confirmación y actualiza BD.
        """
        identificador_cif = encriptar(identificador)

        # SIMULACIÓN (Windows u OS sin GPIO): alterna estado y retorna acción
        if not GPIO_OK:
            print("Simulación: no se controla GPIO.")
            tiene_bici = self.db.obtener_estado_bici(identificador_cif, tipo)
            self.db.actualizar_estado_bici(identificador_cif, not tiene_bici, tipo)
            return "salida" if tiene_bici else "entrada"

        # HARDWARE REAL
        tiene_bici = self.db.obtener_estado_bici(identificador_cif, tipo)

        if tiene_bici:
            # Usuario está sacando la bici -> requiere PIN
            print(f"Usuario {identificador}: solicitud para sacar bicicleta.")
            pin_ingresado = getpass.getpass("Ingresa tu PIN: ")
            if self.db.validar_pin(identificador, pin_ingresado, tipo):
                print("Abriendo Actuador (SALIDA)...")
                energizar(0, 1)  # Giro sentido "abrir"
                ok = self._esperar_movimiento_objetivo("abierto", timeout=8.0)
                desenergizar()
                if not ok:
                    print("Advertencia: no se confirmó 'abierto' por sensores (timeout).")
                self.db.actualizar_estado_bici(identificador_cif, False, tipo)
                return "salida"
            else:
                print("PIN incorrecto. Acceso denegado.")
                return "denegado"
        else:
            # Usuario está guardando la bici -> no requiere PIN
            print(f"Usuario {identificador}: guardando bicicleta (ENTRADA).")
            energizar(1, 0)  # Giro sentido "cerrar"
            ok = self._esperar_movimiento_objetivo("cerrado", timeout=8.0)
            desenergizar()
            if not ok:
                print("Advertencia: no se confirmó 'cerrado' por sensores (timeout).")
            self.db.actualizar_estado_bici(identificador_cif, True, tipo)
            return "entrada"

    # ---------- Registro de NUEVOS usuarios ----------
    def procesar_nuevo_usuario(self, datos: dict, tipo: str):
        """
        Guarda un usuario NO existente en BD según reglas:
        - Alumno 'Inscrito' -> BD
        - Profesor 'Válida' -> BD
        - Si no cumplen, al JSON correspondiente.

        Además:
        - Determina si 'tiene_bici_guardada' = True (si acción fue 'entrada') o False (si 'salida').
        - Actualiza contadores globales.
        """
        from app.models.alumno import Alumno
        from app.models.profesor import Profesor

        datos["fecha"] = str(datetime.datetime.now())
        accion = datos.get("accion", "").lower()
        tiene_bici = True if accion == "entrada" else False

        if tipo == "alumno":
            alumno = Alumno(**datos)
            if alumno.estado == "Inscrito":
                self.db.insertar_alumno(alumno, tiene_bici_guardada=tiene_bici)
                if accion == "salida":
                    ControlAcceso.contador_sal += 1
                elif accion == "entrada":
                    ControlAcceso.contador_ent += 1
                print(f"Nuevo alumno {alumno.boleta} registrado con PIN {alumno.pin}.")
            else:
                self.json.guardar(alumno.to_dict(), "alumno")
                print("Registro de alumno no inscrito guardado en JSON.")
        elif tipo == "profesor":
            profesor = Profesor(**datos)
            if "valida" in norm(profesor.estado):
                self.db.insertar_profesor(profesor, tiene_bici_guardada=tiene_bici)
                if accion == "salida":
                    ControlAcceso.contador_sal += 1
                elif accion == "entrada":
                    ControlAcceso.contador_ent += 1
                print(f"Nuevo profesor {profesor.nombre} registrado con PIN {profesor.pin}.")
            else:
                self.json.guardar(profesor.to_dict(), "profesor")
                print(f"Registro de profesor no válido guardado en JSON. Estado: '{profesor.estado}'")

