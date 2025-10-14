"""
app/hardware/gpio_ctrl.py
-------------------------
Capa de abstracción del hardware GPIO.

Objetivos:
- Si corremos en Linux y existe RPi.GPIO con pines configurados, activamos control real.
- Si NO, caemos en "simulación": las funciones existen, pero no accionan hardware.
- Exponemos funciones simples: leer_estado_actuador(), energizar(), desenergizar(), cleanup().
"""

import warnings
from app.config import SO, PINS

warnings.filterwarnings("ignore")

# Flags y handler de GPIO; si no estamos en Linux o falla el setup, quedará en simulación.
GPIO_OK = False
GPIO = None

if SO == "Linux":
    try:
        import RPi.GPIO as _GPIO
        # Modo BCM para numeración de pines
        _GPIO.setmode(_GPIO.BCM)
        _GPIO.setwarnings(False)

        # Pines de salida (motor/actuador)
        _GPIO.setup(PINS['pin_a'], _GPIO.OUT)
        _GPIO.setup(PINS['pin_b'], _GPIO.OUT)

        # Pines de entrada (sensores de fin de carrera)
        _GPIO.setup(PINS['sensor_abierto'], _GPIO.IN, pull_up_down=_GPIO.PUD_DOWN)
        _GPIO.setup(PINS['sensor_cerrado'], _GPIO.IN, pull_up_down=_GPIO.PUD_DOWN)

        GPIO = _GPIO
        GPIO_OK = True
    except Exception:
        print("GPIO no disponible o pines no configurados. Modo simulación activado.")

def leer_estado_actuador():
    """
    Lee sensores fin de carrera. Devuelve:
    - 'abierto'  : sensor_abierto activo y sensor_cerrado inactivo
    - 'cerrado'  : sensor_cerrado activo y sensor_abierto inactivo
    - 'error'    : estado intermedio/indeterminado (ambos 0 o ambos 1)
    - 'simulado' : si no hay GPIO real
    """
    if not GPIO_OK:
        return "simulado"
    abierto = GPIO.input(PINS['sensor_abierto'])
    cerrado = GPIO.input(PINS['sensor_cerrado'])
    if abierto and not cerrado: return "abierto"
    if cerrado and not abierto: return "cerrado"
    return "error"

def energizar(pin_a_val: int, pin_b_val: int):
    """
    Activa los pines de salida para provocar giro del actuador.
    - Para cerrar (entrada), normalmente (1,0)
    - Para abrir (salida),  normalmente (0,1)
    """
    if GPIO_OK:
        GPIO.output(PINS['pin_a'], pin_a_val)
        GPIO.output(PINS['pin_b'], pin_b_val)

def desenergizar():
    """Apaga ambos pines (detiene el actuador)."""
    if GPIO_OK:
        GPIO.output(PINS['pin_a'], 0)
        GPIO.output(PINS['pin_b'], 0)

def cleanup():
    """Libera los recursos del GPIO (llamar al final del programa)."""
    if GPIO_OK:
        GPIO.cleanup()

