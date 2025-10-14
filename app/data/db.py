"""
app/data/db.py
--------------
Capa de acceso a SQLite:
- Crea tablas alumnos/profesores si no existen.
- Inserta nuevos registros (primer acceso).
- Actualiza acciones y estados (entrada/salida).
- Valida PIN y maneja el flag 'tiene_bici_guardada' por usuario.

Diseño:
- Las columnas sensibles (boleta, curp, numero_empleado, clave_presupuestal) se guardan encriptadas.
- La 'url' es UNIQUE por registro, lo que permite evitar duplicados al escanear.
"""

import sqlite3, datetime
from app.utils.crypto import encriptar, desencriptar

class BaseDatos:
    def __init__(self, archivo: str):
        self.archivo = archivo
        self._crear_tabla()

    def _crear_tabla(self):
        """Crea (si no existen) las tablas 'alumnos' y 'profesores'."""
        with sqlite3.connect(self.archivo) as conn:
            conn.execute("""
            CREATE TABLE IF NOT EXISTS alumnos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                boleta TEXT,                -- ENCRIPTADA
                curp TEXT,                  -- ENCRIPTADA
                nombre TEXT,
                carrera TEXT,
                escuela TEXT,
                estado TEXT,
                turno TEXT,
                fecha TEXT,
                url TEXT UNIQUE,            -- IDENTIFICA EL QR ESCANEADO
                accion TEXT,                -- 'entrada' | 'salida' | ...
                pin TEXT,                   -- PIN en claro (podrías cifrarlo si quieres)
                tiene_bici_guardada INTEGER DEFAULT 0
            )""")
            conn.execute("""
            CREATE TABLE IF NOT EXISTS profesores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                numero_empleado TEXT,       -- ENCRIPTADA
                nombre TEXT,
                clave_presupuestal TEXT,    -- ENCRIPTADA
                area_adscripcion TEXT,
                estado TEXT,
                fecha TEXT,
                url TEXT UNIQUE,
                accion TEXT,
                pin TEXT,
                tiene_bici_guardada INTEGER DEFAULT 0
            )""")

    # ---------- INSERTS (primer registro de un usuario) ----------
    def insertar_alumno(self, alumno, tiene_bici_guardada: bool):
        """Inserta alumno si no existe (OR IGNORE por URL). Guarda cifrados los campos sensibles."""
        with sqlite3.connect(self.archivo) as conn:
            conn.execute("""
            INSERT OR IGNORE INTO alumnos
            (boleta, curp, nombre, carrera, escuela, estado, turno, fecha, url, accion, pin, tiene_bici_guardada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (encriptar(alumno.boleta), encriptar(alumno.curp), alumno.nombre, alumno.carrera,
                  alumno.escuela, alumno.estado, alumno.turno, alumno.fecha,
                  alumno.url, alumno.accion, alumno.pin, 1 if tiene_bici_guardada else 0))

    def insertar_profesor(self, profesor, tiene_bici_guardada: bool):
        """Inserta profesor si no existe (OR IGNORE por URL)."""
        with sqlite3.connect(self.archivo) as conn:
            conn.execute("""
            INSERT OR IGNORE INTO profesores
            (numero_empleado, nombre, clave_presupuestal, area_adscripcion, estado, fecha, url, accion, pin, tiene_bici_guardada)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (encriptar(profesor.numero_empleado), profesor.nombre, encriptar(profesor.clave_presupuestal),
                  profesor.area_adscripcion, profesor.estado, profesor.fecha,
                  profesor.url, profesor.accion, profesor.pin, 1 if tiene_bici_guardada else 0))

    # ---------- CONSULTAS DE EXISTENCIA/IDENTIFICADOR ----------
    def existe_url(self, url: str, tipo: str) -> bool:
        """¿Existe ya esta URL en 'alumnos' o 'profesores'? (para saltar el scrapeo si ya está en BD)"""
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        with sqlite3.connect(self.archivo) as conn:
            c = conn.cursor()
            c.execute(f"SELECT id FROM {tabla} WHERE url = ?", (url,))
            return c.fetchone() is not None

    def obtener_identificador_por_url(self, url: str, tipo: str) -> str | None:
        """
        Dada una URL, devuelve el identificador principal en texto claro:
        - alumno  -> 'boleta'
        - profesor-> 'numero_empleado'
        Retorna None si no encuentra.
        """
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        columna_id = "boleta" if tipo == "alumno" else "numero_empleado"
        with sqlite3.connect(self.archivo) as conn:
            c = conn.cursor()
            c.execute(f"SELECT {columna_id} FROM {tabla} WHERE url = ?", (url,))
            res = c.fetchone()
            return desencriptar(res[0]) if res else None

    # ---------- ACTUALIZACIONES DE ACCIÓN/ESTADO ----------
    def actualizar_accion(self, url: str, accion: str, tipo: str):
        """
        Registra la 'accion' ('entrada'/'salida') y la 'fecha' del evento.
        Además sincroniza 'tiene_bici_guardada' con la acción (entrada->1, salida->0).
        """
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        nuevo_estado_bici = 1 if accion == "entrada" else 0 if accion == "salida" else None
        with sqlite3.connect(self.archivo) as conn:
            if nuevo_estado_bici is None:
                conn.execute(f"UPDATE {tabla} SET accion = ?, fecha = ? WHERE url = ?",
                             (accion, str(datetime.datetime.now()), url))
            else:
                conn.execute(f"UPDATE {tabla} SET accion = ?, fecha = ?, tiene_bici_guardada = ? WHERE url = ?",
                             (accion, str(datetime.datetime.now()), nuevo_estado_bici, url))

    def actualizar_estado_bici(self, identificador_cif: str, nuevo_estado: bool, tipo: str):
        """
        Actualiza el flag 'tiene_bici_guardada' para el usuario (por identificador cifrado).
        Se usa desde ControlAcceso tras mover la cerradura.
        """
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        columna_id = "boleta" if tipo == "alumno" else "numero_empleado"
        with sqlite3.connect(self.archivo) as conn:
            conn.execute(f"UPDATE {tabla} SET tiene_bici_guardada = ? WHERE {columna_id} = ?",
                         (1 if nuevo_estado else 0, identificador_cif))

    # ---------- VALIDACIONES ----------
    def validar_pin(self, identificador: str, pin_ingresado: str, tipo: str) -> bool:
        """
        Verifica el PIN del usuario al 'sacar' bici.
        Importante: comparamos contra el valor guardado en BD (no cifrado).
        El identificador que llega es plano, pero se cifra para buscar.
        """
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        columna_id = "boleta" if tipo == "alumno" else "numero_empleado"
        with sqlite3.connect(self.archivo) as conn:
            c = conn.cursor()
            c.execute(f"SELECT pin FROM {tabla} WHERE {columna_id} = ?", (encriptar(identificador),))
            res = c.fetchone()
            return res and res[0] == pin_ingresado

    def obtener_estado_bici(self, identificador_cif: str, tipo: str) -> bool:
        """
        Lee el flag 'tiene_bici_guardada' (True/False) por identificador cifrado.
        Se usa para decidir si corresponde ENTRADA o SALIDA.
        """
        tabla = "alumnos" if tipo == "alumno" else "profesores"
        columna_id = "boleta" if tipo == "alumno" else "numero_empleado"
        with sqlite3.connect(self.archivo) as conn:
            c = conn.cursor()
            c.execute(f"SELECT tiene_bici_guardada FROM {tabla} WHERE {columna_id} = ?", (identificador_cif,))
            res = c.fetchone()
            return res[0] == 1 if res else False
