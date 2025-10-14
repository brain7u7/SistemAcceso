"""
app/utils/classify.py
---------------------
"Adapter" que reusa TU Clasificador.clasificar_url(url).

Motivo del adaptador:
- Tu función puede devolver "alumno", "profesor", "desconocido" o "conflicto".
- El flujo del sistema solo continúa con "alumno" o "profesor".
- Mapeamos "desconocido"/"conflicto" a None para cortar el flujo de forma limpia.
"""

from typing import Optional
from Clasificador import clasificar_url as _clasificar  # tu implementacion real

def clasificar_url(url: str) -> Optional[str]:
    """
    Retorna 'alumno' | 'profesor' | None
    (None si se recibe 'desconocido' o 'conflicto').
    """
    t = _clasificar(url)
    return t if t in ("alumno", "profesor") else None
