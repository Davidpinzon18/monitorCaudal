# config.py

# --- CREDENCIALES DE LA API DE TUYA (YA PROVISTAS) ---
ACCESS_ID = "TU_ACCESS_ID"
ACCESS_SECRET = "TU_ACCESS_SECRET"

# --- DATOS PENDIENTES (OBLIGATORIO REEMPLAZAR) ---
DEVICE_ID = "TU_DEVICE_ID"
REGION = "us" # Cambie a 'eu', 'cn', etc. si es necesario.

# --- PARÁMETROS DEL TANQUE ---
DIAMETRO_BASE_M = 1.20      # D1: Diámetro de la base (inferior)
DIAMETRO_TAPA_M = 1.40      # D2: Diámetro de la tapa (superior)
ALTURA_TOTAL_M = 1.50       # H: Altura total del tanque
INTERVALO_CONSULTA_S = 60 # Cada cuántos segundos el código preguntará al sensor

# --- PROPIEDADES DE LA TUBERÍA DE SALIDA/ENTRADA ---
# 102.26 mm convertido a metros
DIAMETRO_SALIDA_M = 0.10226