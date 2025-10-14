"""
app/models/alumno.py
--------------------
Contiene el modelo de Alumno. No guarda encriptado aquí; eso se hace en DB.
También genera un PIN por defecto a partir de la boleta (últimos 4 dígitos).
"""

class Alumno:
    def __init__(self, boleta, curp, nombre, carrera, escuela, estado, turno, fecha, url, accion, pin=None):
        self.boleta = boleta
        self.curp = curp
        self.nombre = nombre
        self.carrera = carrera
        self.escuela = escuela
        self.estado = estado
        self.turno = turno
        self.fecha = fecha
        self.url = url
        self.accion = accion
        self.pin = pin or self._generar_pin_desde_boleta()

    def _generar_pin_desde_boleta(self) -> str:
        """
        PIN base: últimos 4 caracteres de la boleta. Si boleta no válida, '0000'.
        (Puedes endurecer esta política si lo necesitas.)
        """
        return self.boleta[-4:] if self.boleta and len(self.boleta) >= 4 else "0000"

    def to_dict(self) -> dict:
        """Serializa a dict para logs o JSON (ojo: no cifra aquí)."""
        return self.__dict__

