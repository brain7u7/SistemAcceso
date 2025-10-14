"""
app/models/profesor.py
----------------------
Modelo de Profesor. Similar a Alumno, su PIN base deriva del número de empleado.
"""

class Profesor:
    def __init__(self, numero_empleado, nombre, clave_presupuestal, area_adscripcion, estado, fecha, url, accion, pin=None):
        self.numero_empleado = numero_empleado
        self.nombre = nombre
        self.clave_presupuestal = clave_presupuestal
        self.area_adscripcion = area_adscripcion
        self.estado = estado
        self.fecha = fecha
        self.url = url
        self.accion = accion
        self.pin = pin or self._generar_pin_desde_numero_empleado()

    def _generar_pin_desde_numero_empleado(self) -> str:
        """PIN base: últimos 4 caracteres del número de empleado, o '0000' si no aplica."""
        return self.numero_empleado[-4:] if self.numero_empleado and len(self.numero_empleado) >= 4 else "0000"

    def to_dict(self) -> dict:
        """Serializa a dict para logs o JSON (no cifra aquí)."""
        return self.__dict__

