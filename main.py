# main.py (CORREGIDO PARA TRONCO DE CONO)

import time
import math
import pandas as pd
from datetime import datetime

import tuya_api
from config import (DIAMETRO_BASE_M,
                    DIAMETRO_TAPA_M,
                    ALTURA_TOTAL_M,  # Nuevos Parámetros
                    INTERVALO_CONSULTA_S,
                    DIAMETRO_SALIDA_M,
                    PENDIENTE_TUBERIA,
                    PESO_ESPECIFICO_AGUA,
                    COTA_EJE_TUBERIA_M,
                    N_MANNING)

# Constantes de radio
RADIO_BASE_M = DIAMETRO_BASE_M / 2
RADIO_TAPA_M = DIAMETRO_TAPA_M / 2

# Base de datos en memoria
db_lecturas = pd.DataFrame(columns=['timestamp_s', 'nivel_m', 'caudal_L_min', 'velocidad_m_s', 'area_actual_m2'])

# Área de la Tubería (en m²) - ESTA ES CONSTANTE
AREA_TUBERIA_M2 = math.pi * (DIAMETRO_SALIDA_M / 2) ** 2


def get_area_en_nivel(h_m):
    """Calcula el área de la sección transversal horizontal en el nivel h."""

    # 1. Tasa de cambio del radio (Pendiente de la pared lateral)
    # Es la variación total del radio dividida por la altura total.
    radio_slope = (RADIO_TAPA_M - RADIO_BASE_M) / ALTURA_TOTAL_M

    # 2. Radio en la altura h
    # Radio(h) = Radio_Base + (Pendiente * Altura_actual)
    radio_actual = RADIO_BASE_M + (radio_slope * h_m)

    # 3. Área del círculo en esa altura
    area_actual = math.pi * (radio_actual ** 2)
    return area_actual


def calcular_caudal_y_reportar():
    global db_lecturas

    nueva_lectura, error = tuya_api.get_current_level()

    if error:
        print(f"Error al obtener nivel: {error}")
        return 0.0, 0.0, 0.0, 0.0, 0.0

    h_actual = nueva_lectura['nivel_m']
    t_actual = nueva_lectura['timestamp_s']
    Q_L_min = 0.0
    V_nivel_m_s = 0.0
    V_flujo_m_s = 0.0
    tiempo_transcurrido = 0.0
    A_actual_M2 = get_area_en_nivel(h_actual)  # ¡Calcula el área usando la fórmula!

    if not db_lecturas.empty:
        ultima_fila = db_lecturas.iloc[-1]
        h_anterior = ultima_fila['nivel_m']
        t_anterior = ultima_fila['timestamp_s']
        A_anterior_M2 = ultima_fila['area_actual_m2']

        # Para el cálculo diferencial, usamos el promedio de las dos áreas (Método del Trapezoide)
        A_promedio_M2 = (A_actual_M2 + A_anterior_M2) / 2

        tiempo_transcurrido = t_actual - t_anterior

        if tiempo_transcurrido > 0:
            delta_h = h_actual - h_anterior

            # 1. Velocidad de cambio del Nivel (m/s)
            V_nivel_m_s = delta_h / tiempo_transcurrido

            # 2. Caudal (Q)
            # Caudal = Área promedio * Delta h / Delta t
            delta_V = A_promedio_M2 * delta_h
            Q_m3_s = delta_V / tiempo_transcurrido
            Q_L_min = Q_m3_s * 60000

            # 3. Velocidad del Flujo en la Tubería (V = Q / A_tubería)
            if abs(Q_m3_s) > 1e-6:
                V_flujo_m_s = abs(Q_m3_s / AREA_TUBERIA_M2)

    # Almacenamiento
    nueva_fila = pd.DataFrame([{'timestamp_s': t_actual,
                                'nivel_m': h_actual,
                                'caudal_L_min': Q_L_min,
                                'velocidad_m_s': V_flujo_m_s,
                                'area_actual_m2': A_actual_M2}])

    db_lecturas = pd.concat([db_lecturas, nueva_fila], ignore_index=True)

    return h_actual, Q_L_min, V_nivel_m_s, V_flujo_m_s, tiempo_transcurrido, A_actual_M2



def calcular_hidraulica_tuberia(nivel_tanque_m):
    """
    Hidráulica de tubería circular parcialmente llena
    Incluye Manning, velocidad teórica y Azevedo Netto
    """

    d = DIAMETRO_SALIDA_M
    r = d / 2

    # Tirante hidráulico
    y = max(0.0, min(nivel_tanque_m - COTA_EJE_TUBERIA_M + r, d))

    if y <= 0:
        return None

    # Ángulo subtendido
    theta = 2 * math.acos(1 - (2 * y / d))

    # Área mojada
    A = (d**2 / 8) * (theta - math.sin(theta))

    # Perímetro mojado
    P = 0.5 * theta * d

    # Radio hidráulico
    R = A / P

    # Ancho superficial
    T = d * math.sin(theta / 2)

    # Esfuerzo cortante
    if PENDIENTE_TUBERIA < 0.10:
        tau = PESO_ESPECIFICO_AGUA * R * PENDIENTE_TUBERIA
    else:
        tau = PESO_ESPECIFICO_AGUA * R * math.sin(math.atan(PENDIENTE_TUBERIA))

    # ----------------------------
    # VELOCIDAD TEÓRICA (MANNING)
    # V = (1/n) * R^(2/3) * S^(1/2)
    # ----------------------------
    V_manning = (1 / N_MANNING) * (R ** (2 / 3)) * (PENDIENTE_TUBERIA ** 0.5)

    # Caudal por Manning
    Q_manning_m3_s = A * V_manning
    Q_manning_L_s = Q_manning_m3_s * 1000

    # ----------------------------
    # CAUDAL DE AZEVEDO NETTO
    # Q = 0.375 * D^2.667 * S^0.5
    # ----------------------------
    Q_azevedo_m3_s = 0.375 * (d ** 2.667) * (PENDIENTE_TUBERIA ** 0.5)
    Q_azevedo_L_s = Q_azevedo_m3_s * 1000

    return {
        "tirante_m": y,
        "angulo_rad": theta,
        "area_m2": A,
        "perimetro_m": P,
        "radio_hidraulico_m": R,
        "ancho_superficial_m": T,
        "esfuerzo_cortante_N_m2": tau,
        "velocidad_manning_m_s": V_manning,
        "caudal_manning_L_s": Q_manning_L_s,
        "caudal_azevedo_L_s": Q_azevedo_L_s
    }




# Bucle de Ejecución Principal
if __name__ == "__main__":

    if not tuya_api.initialize_tuya():
        exit()

    print(f"--- Sistema de Monitoreo de Caudal Iniciado (Tanque Tronco de Cono) ---")
    print(f"Geometría: Base {DIAMETRO_BASE_M}m | Tapa {DIAMETRO_TAPA_M}m | Altura {ALTURA_TOTAL_M}m")
    print(f"Tubería PVC (Diámetro: {DIAMETRO_SALIDA_M * 1000:.2f} mm)")

    while True:
        try:
            nivel, caudal, V_nivel_m_s, V_flujo_m_s, tiempo_transcurrido, area_actual = calcular_caudal_y_reportar()

            if tiempo_transcurrido > 0:
                print()
                print(f"=" * 50)
                estado = "ENTRADA" if caudal > 0.01 else ("SALIDA" if caudal < -0.01 else "ESTABLE")
                print(f"-" * 50)

                print(f"[{datetime.now().strftime('%H:%M:%S')}]")
                print(f"|-- Nivel: {nivel:.3f} m (Área del agua: {area_actual:.3f} m²)")
                print(f"|-- Caudal ({estado}): {abs(caudal):.2f} Litros/Minuto")
                print(f"|-- Vel. Cambio Nivel: {V_nivel_m_s * 60:.4f} m/min")
                print(f"|-- Vel. Flujo Tubería: {V_flujo_m_s:.2f} m/s")

                hidraulica = calcular_hidraulica_tuberia(nivel)

                if hidraulica:
                    print(f"=" * 50)

                    print("|-- Hidráulica Tubería:")
                    print(f"-" * 50)
                    print(f"    Tirante: {hidraulica['tirante_m']:.3f} m")
                    print(f"    Tirante: {hidraulica['angulo_rad']:.3f} m")
                    print(f"    Área mojada: {hidraulica['area_m2']:.4f} m²")
                    print(f"    Radio hidráulico: {hidraulica['radio_hidraulico_m']:.4f} m")
                    print(f"    Ancho superficial: {hidraulica['ancho_superficial_m']:.3f} m")
                    print(f"    Esfuerzo cortante: {hidraulica['esfuerzo_cortante_N_m2']:.2f} N/m²")
                    print(f"    Velocidad (Manning): {hidraulica['velocidad_manning_m_s']:.3f} m/s")
                    print(f"    Caudal (Manning): {hidraulica['caudal_manning_L_s']:.2f} L/s")
                    print(f"    Caudal (Azevedo Netto): {hidraulica['caudal_azevedo_L_s']:.2f} L/s")

            else:
                print(
                    f"[{datetime.now().strftime('%H:%M:%S')}] Nivel: {nivel:.3f} m | Esperando la segunda lectura para calcular...")

            time.sleep(INTERVALO_CONSULTA_S)

        except KeyboardInterrupt:
            print("\nProceso detenido por el usuario.")
            break
        except Exception as e:
            print(f"Error inesperado: {e}")
            time.sleep(INTERVALO_CONSULTA_S)