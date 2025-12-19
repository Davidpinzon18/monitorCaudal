# config.py

# --- CREDENCIALES DE LA API DE TUYA (YA PROVISTAS) ---
ACCESS_ID = "TU_ACCESS_ID"
ACCESS_SECRET = "TU_ACCESS_SECRET"

# --- DATOS PENDIENTES (OBLIGATORIO REEMPLAZAR) ---
DEVICE_ID = "TU_DEVICE_ID"
REGION = "us" # Cambie a 'eu', 'cn', etc. si es necesario.

# --- PARÁMETROS DEL TANQUE ---
DIAMETRO_BASE_M = 0.37      # D1: Diámetro de la base (inferior)
DIAMETRO_TAPA_M = 0.37      # D2: Diámetro de la tapa (superior)
ALTURA_TOTAL_M = 0.215       # H: Altura total del tanque
INTERVALO_CONSULTA_S = 60 # Cada cuántos segundos el código preguntará al sensor

# --- HIDRÁULICA DE LA TUBERÍA ---
PENDIENTE_TUBERIA = 0.01      # S (m/m)
PESO_ESPECIFICO_AGUA = 9810   # γ (N/m³)
COTA_EJE_TUBERIA_M = 0.20     # Altura del eje de la tubería desde el fondo del tanque

# --- PARÁMETROS HIDRÁULICOS ---
# PVC: 0.009 – 0.013
# Concreto: 0.013 – 0.015
N_MANNING = 0.013       # Coeficiente de rugosidad (PVC típico)



# --- PROPIEDADES DE LA TUBERÍA DE SALIDA/ENTRADA ---
# 102.26 mm convertido a metros
DIAMETRO_SALIDA_M = 0.10226