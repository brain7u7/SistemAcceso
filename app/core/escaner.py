"""
app/core/escaner.py
-------------------
Flujo por escaneo (HID/console):
1) Normaliza URL.
2) Checa si la URL está BLOQUEADA -> aborta si lo está.
3) Clasifica (alumno/profesor); si None, corta.
4) Si está en BD -> abrir_cerradura + actualizar_accion.
5) Si NO está en BD -> obtener HTML, extraer datos, abrir_cerradura, registrar nuevo.
"""

import time
from app.web.scraper import normalizar_url, obtener_html, extraer_datos_alumno, extraer_datos_profesor
from app.utils.classify import clasificar_url
from app.config import CONFIG

class EscanerQR:
    def __init__(self, acceso, db):
        self.acceso = acceso
        self.db = db
        self.vistos = {}
        self.modo_operacion = CONFIG.get("modo_operacion", "hid")

    def procesar_url(self, url: str, tipo: str):
        ahora = time.time()
        if url in self.vistos and (ahora - self.vistos[url]) < CONFIG['tiempo_anti_rebote_seg']:
            print("Escaneo repetido ignorado.")
            return
        self.vistos[url] = ahora

        # --- 0) Bloqueados por URL ---
        # Si config.json tiene archivo de bloqueados y la URL está listada, negamos.
        try:
            if hasattr(self.acceso, "json") and self.acceso.json.url_bloqueada(url):
                print("Acceso denegado: URL bloqueada.")
                return
        except Exception:
            # Si no hay archivo de bloqueados o no está inicializado, seguimos normal.
            pass

        # --- 1) ¿Existe ya en BD? ---
        if self.db.existe_url(url, tipo):
            print("Usuario ya registrado. Verificando acceso desde la base de datos...")
            identificador = self.db.obtener_identificador_por_url(url, tipo)
            if not identificador:
                print("Error: URL existe pero no se pudo recuperar el identificador.")
                return

            accion = self.acceso.abrir_cerradura(identificador, tipo)
            if accion != "denegado":
                self.db.actualizar_accion(url, accion, tipo)
                print(f"Acceso '{accion}' registrado para usuario {identificador}.")
                if accion == "salida":
                    self.acceso.contador_sal += 1
                elif accion == "entrada":
                    self.acceso.contador_ent += 1
                print(f"Entradas: {self.acceso.contador_ent} | Salidas: {self.acceso.contador_sal}")
        else:
            # --- 2) Usuario NUEVO -> Scraping ---
            print("Usuario nuevo. Realizando consulta web...")
            html = obtener_html(url, user_agent=CONFIG['user_agent'])
            if not html:
                return

            datos = extraer_datos_alumno(html) if tipo == 'alumno' else extraer_datos_profesor(html)
            identificador = datos.get("boleta") if tipo == 'alumno' else datos.get("numero_empleado")
            if not identificador:
                print("No se pudo extraer un identificador válido (boleta/no. empleado).")
                return

            # Bloqueo por identificador (opcional), si existe archivo de bloqueados
            try:
                tipo_id = "boleta" if tipo == "alumno" else "numero_empleado"
                if hasattr(self.acceso, "json") and self.acceso.json.id_bloqueado(tipo_id, identificador):
                    print(f"Acceso denegado: {tipo_id} bloqueado.")
                    return
            except Exception:
                pass

            datos["url"] = url
            accion = self.acceso.abrir_cerradura(identificador, tipo)
            if accion != "denegado":
                datos["accion"] = accion
                self.acceso.procesar_nuevo_usuario(datos, tipo)
                print(f"Entradas: {self.acceso.contador_ent} | Salidas: {self.acceso.contador_sal}")

    def iniciar(self):
        print(f"Sistema listo en modo '{self.modo_operacion}'... (Ctrl+C para salir).")
        try:
            while True:
                # En modo 'hid' seguimos leyendo por consola (simulación de lector HID).
                qr_data = input().strip()
                if not qr_data:
                    continue
                url = normalizar_url(qr_data)
                tipo = clasificar_url(url)  # 'alumno' | 'profesor' | None
                if tipo:
                    self.procesar_url(url, tipo)
                else:
                    print(f"URL no clasificada: {url}")
        except KeyboardInterrupt:
            print("\nSaliendo...")
