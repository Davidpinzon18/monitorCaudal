# tuya_api.py

from tuya_connector import TuyaOpenAPI
import time
from config import ACCESS_ID, ACCESS_SECRET, DEVICE_ID, REGION
from datetime import datetime, timezone


# Mapeo de la región al endpoint de la API
ENDPOINT = f"https://openapi.tuya{REGION}.com"

# Inicializar la API.
openapi = TuyaOpenAPI(ENDPOINT, ACCESS_ID, ACCESS_SECRET)


def initialize_tuya():
    """Conecta a Tuya y obtiene el primer token de acceso."""
    print(f"Intentando conectar a Tuya API en la región: {REGION}...")
    if openapi.connect():
        print("Conexión y Autenticación de Tuya exitosa.")
        return True
    else:
        print("!!! ERROR: Fallo en la conexión a Tuya. Revise Client ID/Secret y Region en config.py.")
        return False


def get_current_level():
    """Consulta la API de Tuya para obtener el nivel actual del sensor."""

    # ¡NUEVA RUTA DE LA API que resolvió el token invalid!
    url = f"/v1.0/iot-03/devices/{DEVICE_ID}/status"

    try:
        response = openapi.get(url)

        #print(f"Este es el status: {response}") # Deje esta línea si quiere seguir viendo el JSON

        # Convertir de milisegundos a segundos
        fecha_utc = datetime.fromtimestamp(response.get('t') / 1000, tz=timezone.utc)

        # Mostrar en UTC
        print("\n\n")
        print("+"*50)
        print("")
        print("UTC:", fecha_utc)

        # Convertir a hora local de Colombia (UTC-5)
        from datetime import timedelta
        fecha_colombia = fecha_utc.astimezone(timezone(timedelta(hours=-5)))
        print("Colombia:", fecha_colombia)

        if response.get('success', False):
            status_list = response.get('result', [])
            nivel_encontrado = None

            # Buscar el código del nivel, que en el JSON es 'liquid_depth'
            for item in status_list:
                if item['code'] == 'liquid_depth':  # ¡Usamos el código exacto!
                    nivel_cm = item['value']
                    nivel_encontrado = float(nivel_cm) / 100.0  # Convertir cm a metros
                    break

            if nivel_encontrado is not None:
                timestamp_s = time.time()
                return {'nivel_m': nivel_encontrado, 'timestamp_s': timestamp_s}, None
            else:
                return None, "Error: No se encontró el código 'liquid_depth' en la respuesta de Tuya."
        else:
            return None, f"Fallo al obtener estado. Mensaje: {response.get('msg', 'Error desconocido')}"

    except Exception as e:
        return None, f"Error en la consulta de API: {e}"