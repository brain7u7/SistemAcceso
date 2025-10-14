"""
app/web/scraper.py
------------------
Funciones para:
- Normalizar la URL leída del QR (corrige caracteres alterados).
- Descargar HTML con 'requests'.
- Extraer datos de ALUMNO y PROFESOR desde el HTML con selectores flexibles.

Notas:
- verify=False por contexto del proyecto original (certificados a veces no válidos).
- user-agent configurable desde config.json.
"""

from urllib.parse import urlparse
import requests
from bs4 import BeautifulSoup
from app.utils.text import norm

def normalizar_url(qr_data: str) -> str:
    """
    Corrige errores comunes en la cadena del QR:
    - 'httpsñ--' o 'httpsÑ--' -> 'https://'
    - '.mx-vcred-'             -> '.mx/vcred/'
    - '_h¿'                    -> '?h='
    """
    if not qr_data:
        return qr_data
    return (qr_data.replace("httpsñ--", "https://")
                  .replace("httpsÑ--", "https://")
                  .replace(".mx-vcred-", ".mx/vcred/")
                  .replace("_h¿", "?h="))

def obtener_html(url: str, user_agent: str, timeout: int = 60) -> str | None:
    """
    Descarga HTML si la URL tiene esquema http/https. Maneja excepciones de red
    y devuelve None si falla, para que el flujo superior sepa abortar.
    """
    try:
        if urlparse(url).scheme not in ("http", "https"):
            return None
        r = requests.get(url, headers={"User-Agent": user_agent}, timeout=timeout, verify=False)
        r.raise_for_status()
        return r.text
    except requests.RequestException as e:
        print(f"Error al obtener HTML de {url}: {e}")
        return None

def _texto(o) -> str:
    """Helper: texto plano de un nodo (string), juntando con espacios y strip=True."""
    return o.get_text(" ", strip=True) if o else ""

def extraer_datos_alumno(html: str) -> dict:
    """
    Intenta extraer campos típicos del portal de alumno. Los selectores son flexibles.
    """
    sopa = BeautifulSoup(html, "lxml")
    datos = {
        "boleta": _texto(sopa.select_one("div.boleta")),
        "curp": _texto(sopa.select_one("div.curp")),
        "nombre": _texto(sopa.select_one("div.nombre")),
        "carrera": _texto(sopa.select_one("div.carrera")),
        "escuela": _texto(sopa.select_one("div.escuela")),
        "estado": "",
        "turno": ""
    }
    # Bloque con fondo: suele tener estado e incluso el "Turno"
    estado_bloque = sopa.select_one('div[style*="background-color"]')
    if estado_bloque:
        texto = _texto(estado_bloque)
        datos["estado"] = "Inscrito" if "Inscrito" in texto else texto
        if "Turno:" in texto:
            datos["turno"] = texto.split("Turno:")[-1].strip()
    return datos

def extraer_datos_profesor(html: str) -> dict:
    """
    Extrae campos del portal de profesor. La página puede variar, así que:
    - Buscamos etiquetas comunes ('span.card', 'label', 'strong') como "Nombre", "Número de empleado", etc.
    - Para el ESTADO validamos por clase CSS 'alert-success' (válida) o 'alert-danger' (no válida).
    - Normalizamos texto para comparar sin tildes.
    """
    sopa = BeautifulSoup(html, "lxml")
    datos = {
        "numero_empleado": "",
        "nombre": "",
        "clave_presupuestal": "",
        "area_adscripcion": "",
        "estado": "No válida"
    }

    # Campos: heurística flexible
    posibles_spans = sopa.select("span.card, label, span, strong")
    for span in posibles_spans:
        label = _texto(span)
        if not label:
            continue
        # Valor probable: siguiente hermano razonable
        val = ""
        sib = span.find_next(["div", "span"])
        if sib:
            val = _texto(sib)

        nlabel = norm(label)
        if "numero" in nlabel and "empleado" in nlabel:
            datos["numero_empleado"] = val
        elif "nombre" in nlabel and not datos["nombre"]:
            datos["nombre"] = val
        elif "clave" in nlabel and "presupuestal" in nlabel:
            datos["clave_presupuestal"] = val
        elif ("area" in nlabel and "adscripcion" in nlabel) or ("adscripcion" in nlabel):
            datos["area_adscripcion"] = val

    # Estado a partir de clases Bootstrap-like
    ok = sopa.select_one(".alert-success") or sopa.find(
        lambda tag: tag.name in ["div", "h3", "span"] and "alert-success" in (tag.get("class") or [])
    )
    if ok and "valida" in norm(ok.get_text(" ", strip=True)):
        datos["estado"] = "Válida"
    else:
        bad = sopa.select_one(".alert-danger") or sopa.find(
            lambda tag: tag.name in ["div", "h3", "span"] and "alert-danger" in (tag.get("class") or [])
        )
        if bad and ("no valida" in norm(bad.get_text(" ", strip=True)) or "invalida" in norm(bad.get_text(" ", strip=True))):
            datos["estado"] = "No válida"

    return datos

