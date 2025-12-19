import time
import math
import pandas as pd
from datetime import datetime

import tuya_api
from config import (DIAMETRO_BASE_M,
                    DIAMETRO_TAPA_M,
                    ALTURA_TOTAL_M,
                    INTERVALO_CONSULTA_S,
                    DIAMETRO_SALIDA_M,
                    PENDIENTE_TUBERIA,
                    PESO_ESPECIFICO_AGUA,
                    COTA_EJE_TUBERIA_M,
                    N_MANNING)

# Constantes de radio
RADIO_BASE_M = DIAMETRO_BASE_M / 2
RADIO_TAPA_M = DIAMETRO_TAPA_M / 2
AREA_TUBERIA_M2 = math.pi * (DIAMETRO_SALIDA_M / 2) ** 2

# Base de datos en memoria para cálculo diferencial
db_lecturas = pd.DataFrame(columns=['timestamp_s', 'nivel_m', 'caudal_L_min', 'velocidad_m_s', 'area_actual_m2'])


def get_area_en_nivel(h_m):
    """Calcula el área de la sección transversal horizontal en el nivel h (Tronco de cono)."""
    if ALTURA_TOTAL_M <= 0: return math.pi * (RADIO_BASE_M ** 2)
    # Pendiente de la pared lateral
    radio_slope = (RADIO_TAPA_M - RADIO_BASE_M) / ALTURA_TOTAL_M
    # Radio a la altura actual: R(h) = R_base + slope * h
    radio_actual = RADIO_BASE_M + (radio_slope * h_m)
    return math.pi * (radio_actual ** 2)


def calcular_hidraulica_tuberia(nivel_tanque_m):
    """Hidráulica de tubería circular parcialmente llena mediante Manning y Azevedo Netto."""
    d = DIAMETRO_SALIDA_M
    r = d / 2.0
    # La batea (invert) es el fondo interno del tubo
    cota_batea = COTA_EJE_TUBERIA_M - r
    y = nivel_tanque_m - cota_batea

    # Inicialización de diccionario de retorno
    res = {
        "estado": "seco", "tirante_m": 0.0, "theta": 0.0, "area_m2": 0.0,
        "perimetro_m": 0.0, "radio_h_m": 0.0, "ancho_m": 0.0, "tau": 0.0,
        "v_manning": 0.0, "q_manning_m3s": 0.0, "q_azevedo_m3s": 0.0
    }

    if y > 1e-6:
        y = min(y, d)  # Capar a tubería llena
        res["estado"] = "parcial" if y < d else "llena"
        res["tirante_m"] = y

        # Ángulo subtendido theta:
        # $$\theta = 2 \cdot \arccos(1 - \frac{2y}{d})$$
        arg = 1.0 - (2.0 * y / d)
        theta = 2.0 * math.acos(max(-1.0, min(1.0, arg)))
        res["theta"] = theta

        # Área mojada: $$A = \frac{d^2}{8}(\theta - \sin \theta)$$
        res["area_m2"] = (d ** 2 / 8.0) * (theta - math.sin(theta))
        res["perimetro_m"] = 0.5 * theta * d
        res["radio_h_m"] = res["area_m2"] / res["perimetro_m"] if res["perimetro_m"] > 0 else 0
        res["ancho_m"] = d * math.sin(theta / 2.0)

        # Esfuerzo cortante: $$\tau = \gamma \cdot R_h \cdot S$$
        res["tau"] = PESO_ESPECIFICO_AGUA * res["radio_h_m"] * PENDIENTE_TUBERIA

        # Manning: $$V = \frac{1}{n} R_h^{2/3} S^{1/2}$$
        res["v_manning"] = (1.0 / N_MANNING) * (res["radio_h_m"] ** (2 / 3)) * (PENDIENTE_TUBERIA ** 0.5)
        res["q_manning_m3s"] = res["area_m2"] * res["v_manning"]

        # Azevedo Netto (Capacidad teórica máxima): $$Q = 0.375 \cdot D^{2.667} \cdot S^{0.5}$$
        res["q_azevedo_m3s"] = 0.375 * (d ** 2.667) * (PENDIENTE_TUBERIA ** 0.5)

    return res


def calcular_caudal_y_reportar():
    global db_lecturas
    nueva_lectura, error = tuya_api.get_current_level()  #
    if error: return None

    h_actual = nueva_lectura['nivel_m']
    t_actual = nueva_lectura['timestamp_s']
    A_actual_M2 = get_area_en_nivel(h_actual)

    q_l_min = 0.0
    v_nivel_ms = 0.0
    v_flujo_ms = 0.0
    dt = 0.0

    if not db_lecturas.empty:
        u = db_lecturas.iloc[-1]
        dt = t_actual - u['timestamp_s']
        if dt > 0:
            # Método del Trapezoide para volumen diferencial
            a_prom = (A_actual_M2 + u['area_actual_m2']) / 2
            dh = h_actual - u['nivel_m']
            v_nivel_ms = dh / dt
            q_m3s = (a_prom * dh) / dt
            q_l_min = q_m3s * 60000
            if abs(q_m3s) > 1e-7:
                v_flujo_ms = abs(q_m3s / AREA_TUBERIA_M2)

    nueva_fila = pd.DataFrame([{'timestamp_s': t_actual, 'nivel_m': h_actual,
                                'caudal_L_min': q_l_min, 'velocidad_m_s': v_flujo_ms,
                                'area_actual_m2': A_actual_M2}])
    db_lecturas = pd.concat([db_lecturas, nueva_fila], ignore_index=True)
    return h_actual, q_l_min, v_nivel_ms, v_flujo_ms, dt, A_actual_M2


if __name__ == "__main__":
    if not tuya_api.initialize_tuya(): exit()

    print(f"--- Sistema Monitoreo: {DIAMETRO_BASE_M}m a {DIAMETRO_TAPA_M}m ---")

    while True:
        try:
            res = calcular_caudal_y_reportar()
            if res:
                h, q, vn, vf, dt, area = res
                if dt > 0:
                    hid = calcular_hidraulica_tuberia(h)
                    estado_t = "ENTRADA" if q > 0.01 else ("SALIDA" if q < -0.01 else "ESTABLE")

                    # --- ESTRUCTURA DE REPORTE SOLICITADA ---
                    print(f"\n[{datetime.now().strftime('%H:%M:%S')}]")
                    print(f"|-- Nivel: {h:.3f} m (Área del agua: {area:.3f} m²)")
                    print(f"|-- Caudal ({estado_t}): {abs(q):.2f} Litros/Minuto")
                    print(f"|-- Vel. Cambio Nivel: {vn * 60:.4f} m/min")
                    print(f"|-- Vel. Flujo Tubería: {vf:.2f} m/s")
                    print("=" * 50)
                    print("|-- Hidráulica Tubería:")
                    print("-" * 50)
                    print(f"    Estado: {hid['estado']}")
                    print(f"    Tirante (y): {hid['tirante_m']:.3f} m")
                    print(f"    Theta (rad): {hid['theta']:.4f} rad")
                    print(f"    Área mojada: {hid['area_m2']:.6f} m²")
                    print(f"    Perímetro mojado: {hid['perimetro_m']:.4f} m")
                    print(f"    Radio hidráulico: {hid['radio_h_m']:.6f} m")
                    print(f"    Ancho superficial: {hid['ancho_m']:.4f} m")
                    print(f"    Esfuerzo cortante: {hid['tau']:.3f} N/m²")
                    print(f"    Velocidad (Manning): {hid['v_manning']:.4f} m/s")
                    print(
                        f"    Caudal (Manning): {hid['q_manning_m3s']:.6f} m³/s | {hid['q_manning_m3s'] * 1000:.3f} L/s | {hid['q_manning_m3s'] * 60000:.2f} L/min")
                    print(
                        f"    Caudal (Azevedo Netto): {hid['q_azevedo_m3s']:.6f} m³/s | {hid['q_azevedo_m3s'] * 1000:.3f} L/s | {hid['q_azevedo_m3s'] * 60000:.2f} L/min")
                    print("=" * 50)
                    print(f"    Caudal medido (nivel->caudal): {q:.2f} L/min")
                    print(f"    Diff (medido - Manning) [L/min]: {q - (hid['q_manning_m3s'] * 60000):.2f}")
                else:
                    print(f"[{datetime.now().strftime('%H:%M:%S')}] Esperando segunda lectura...")

            time.sleep(INTERVALO_CONSULTA_S)
        except KeyboardInterrupt:
            break
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(INTERVALO_CONSULTA_S)