from urllib.parse import urlparse
from typing import Literal

TipoURL = Literal["alumno", "profesor", "desconocido", "conflicto"]

PALABRAS_CLAVE = {
    "alumno": ("dae",),
    "profesor": ("dsapp",),
}

def clasificar_url(url: str) -> TipoURL:
    """Clasifica una URL como 'alumno', 'profesor', 'desconocido' o 'conflicto'."""
    try:
        p = urlparse(url if "://" in url else "https://" + url)
        texto = f"{p.netloc}{p.path}{p.query}".lower()
    except Exception:
        texto = url.lower()

    hallazgos = {
        etiqueta
        for etiqueta, claves in PALABRAS_CLAVE.items()
        if any(clave in texto for clave in claves)
    }

    if len(hallazgos) == 1:
        return next(iter(hallazgos))
    elif len(hallazgos) > 1:
        return "conflicto"
    else:
        return "desconocido"

def pedir_y_clasificar() -> None:
    """Pide UNA URL por consola, muestra su clasificación y termina."""
    try:
        url = input("Inserte URL: ").strip()
    except (EOFError, KeyboardInterrupt):
        print("\nSaliendo...")
        return

    if not url:
        print("No se ingresó URL.")
        return

    print(f"Resultado: {clasificar_url(url)}")

if __name__ == "__main__":
    pedir_y_clasificar()
