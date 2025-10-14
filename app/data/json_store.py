"""
app/data/json_store.py
----------------------
Persistencia simple en JSON para:
- Alumnos NO INSCRITOS
- Profesores NO VÁLIDOS
- Lista de BLOQUEADOS (opcional)

'BLOQUEADOS' puede usarse para negar acceso antes de scrapear/consultar BD.
Puedes almacenar objetos tipo:
  { "tipo": "url", "valor": "<la_url>" }
  { "tipo": "boleta", "valor": "20201234" }
  { "tipo": "numero_empleado", "valor": "12345" }
"""

import json
from pathlib import Path

class GestorJSON:
    def __init__(self, archivo_alumnos: str, archivo_profesores: str, archivo_bloqueados: str | None = None):
        self.archivo_alumnos = archivo_alumnos
        self.archivo_profesores = archivo_profesores
        self.archivo_bloqueados = archivo_bloqueados  # puede ser None

    # ---------- util interna ----------
    def _append(self, ruta: str, item: dict):
        p = Path(ruta)
        try:
            if p.exists():
                data = json.loads(p.read_text(encoding="utf-8"))
                if not isinstance(data, list):
                    data = []
            else:
                data = []
        except json.JSONDecodeError:
            data = []
        data.append(item)
        p.write_text(json.dumps(data, ensure_ascii=False, indent=4), encoding="utf-8")

    def _read_list(self, ruta: str) -> list:
        p = Path(ruta)
        if not p.exists():
            return []
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            return data if isinstance(data, list) else []
        except json.JSONDecodeError:
            return []

    # ---------- API pública ----------
    def guardar(self, datos_dict: dict, tipo: str):
        """Guarda un registro en el JSON correspondiente ('alumno' o 'profesor')."""
        archivo = self.archivo_alumnos if tipo == 'alumno' else self.archivo_profesores
        self._append(archivo, datos_dict)

    # BLOQUEADOS
    def agregar_bloqueado(self, tipo: str, valor: str, motivo: str = ""):
        """Agrega un objeto bloqueado. Requiere tener archivo_bloqueados configurado."""
        if not self.archivo_bloqueados:
            return
        self._append(self.archivo_bloqueados, {"tipo": tipo, "valor": valor, "motivo": motivo})

    def lista_bloqueados(self) -> list:
        """Devuelve la lista de bloqueados (puede estar vacía)."""
        if not self.archivo_bloqueados:
            return []
        return self._read_list(self.archivo_bloqueados)

    # Atajos útiles
    def url_bloqueada(self, url: str) -> bool:
        for item in self.lista_bloqueados():
            if item.get("tipo") == "url" and item.get("valor") == url:
                return True
        return False

    def id_bloqueado(self, tipo_id: str, valor: str) -> bool:
        """tipo_id: 'boleta' | 'numero_empleado' (u otro que tú definas)"""
        for item in self.lista_bloqueados():
            if item.get("tipo") == tipo_id and item.get("valor") == valor:
                return True
        return False
