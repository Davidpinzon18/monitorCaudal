# 💧 Monitor de Caudal y Nivel de Tanque (Tuya IoT)

Este proyecto permite monitorear en tiempo real el **nivel de agua** de
un tanque con forma de **tronco de cono**, utilizando un sensor
ultrasónico conectado a la nube mediante **Tuya IoT**.

A partir del nivel del agua, el sistema calcula:

-   Área transversal real del agua (depende de la altura).\
-   Caudal neto (entrada, salida o estable).\
-   Velocidad de cambio de nivel.\
-   Velocidad del flujo dentro de la tubería PVC de salida.

Incluye dos modos de operación: **Polling** (estable) y **WebSocket**
(tiempo real).

------------------------------------------------------------------------

## 📐 Geometría del Tanque

El tanque tiene forma de **tronco de cono**, por lo que el área
superficial del agua **cambia según el nivel**, lo cual hace que el
cálculo del caudal sea preciso.

  -----------------------------------------------------------------------
  Parámetro               Valor            Descripción
  ----------------------- ---------------- ------------------------------
  **Base (D₁)**           1.20 m           Diámetro inferior

  **Tapa (D₂)**           1.40 m           Diámetro superior

  **Altura total (H)**    1.50 m           Altura vertical del tanque

  **Tubería PVC (Dₚ)**    102.26 mm        Usada para calcular velocidad
                                           del flujo
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 🛠️ Requisitos e Instalación

### 1. Requisitos de Software

-   Python **3.8+**
-   Cuenta activa en **Tuya IoT Developer Center**
-   Credenciales del proyecto:
    -   Access ID\
    -   Access Secret\
    -   Device ID

### 2. Instalación de Dependencias

Instale las librerías necesarias:

``` bash
pip install -r requirements.txt
```

------------------------------------------------------------------------

## ⚙️ Configuración

Edite el archivo **config.py** con sus credenciales y parámetros
físicos:

``` python
# --- CREDENCIALES DE LA API DE TUYA ---
ACCESS_ID = "TU_ACCESS_ID"
ACCESS_SECRET = "TU_ACCESS_SECRET"
DEVICE_ID = "TU_DEVICE_ID"
REGION = "us"  # 'us' para Western America Data Center

# --- PARÁMETROS DEL TANQUE CÓNICO/TRONCO DE CONO ---
DIAMETRO_BASE_M = 1.20
DIAMETRO_TAPA_M = 1.40
ALTURA_TOTAL_M = 1.50

# --- PROPIEDADES DE LA TUBERÍA DE SALIDA/ENTRADA ---
DIAMETRO_SALIDA_M = 0.10226

# --- CONFIGURACIÓN DE LOS MODOS ---
INTERVALO_CONSULTA_S = 60  # Recomendado para estabilidad
```

------------------------------------------------------------------------

## 💻 Uso del Programa

Ejecute el sistema:

``` bash
python main.py
```

### Menú Inicial

El programa permite elegir entre dos modos:

### 1️⃣ **Polling (Intervalo fijo)**

-   Más estable\
-   Ideal para cálculos confiables de caudal\
-   Lee el sensor cada `INTERVALO_CONSULTA_S` (ej: 60s)

### 2️⃣ **WebSocket (Tiempo real)**

-   Actualizaciones instantáneas\
-   Más sensible al ruido del sensor

------------------------------------------------------------------------

## 📊 Salida de Datos

Ejemplo de salida en consola:

    [12:45:10]
    |-- Nivel: 1.350 m (Área del agua: 1.517 m²)
    |-- Caudal (SALIDA): 7.50 Litros/Minuto
    |-- Vel. Cambio Nivel: -0.0039 m/min
    |-- Vel. Flujo Tubería: 0.01 m/s

------------------------------------------------------------------------

## ⚙️ Arquitectura del Software

El proyecto está dividido en módulos:

  -----------------------------------------------------------------------
  Archivo                  Responsabilidad
  ------------------------ ----------------------------------------------
  **config.py**            Variables globales, parámetros físicos,
                           credenciales

  **tuya_api.py**          Comunicación con Tuya: autenticación, polling,
                           WebSocket

  **main.py**              Lógica central, menú, fórmulas del tanque,
                           cálculos de caudal
  -----------------------------------------------------------------------

------------------------------------------------------------------------

## 📝 Notas Importantes

-   **Inestabilidad del sensor**: Si el intervalo de lectura es muy
    corto (ej. 10s), el sensor ultrasónico puede generar ruido.\
    → Use **Polling 60s** para resultados confiables.

-   **Filtro de ruido incluido**:\
    El sistema **ignora cambios superiores a 50 cm** entre mediciones
    porque se consideran errores del sensor.
