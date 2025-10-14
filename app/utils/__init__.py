"""
app/utils/__init__.py
---------------------
Re-exporta funciones utilitarias para imports más simples:
    from app.utils import encriptar, desencriptar, clasificar_url, norm
"""

from .crypto import encriptar, desencriptar
from .classify import clasificar_url
from .text import norm

__all__ = ["encriptar", "desencriptar", "clasificar_url", "norm"]
