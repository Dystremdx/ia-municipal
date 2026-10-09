"""
=============================================================================
PROYECTO: IA Municipal · Priorización Inteligente
CURSO: Gestión de Proyectos TICs (EST315)
CLIENTE: Municipalidad de Lima (Simulado)
EQUIPO:
  - Project Manager: Cristian Ronaldo
  - Análisis de Datos: Ronald Wilder
  - Arquitectura IA: Yair Dilan
  - Comunicaciones: Choucha
ARCHIVO: motor_ia.py
DESCRIPCIÓN:
  Motor de Inteligencia Artificial y reglas de negocio para la priorización
  automática de reportes de incidencias municipales. Normaliza factores,
  aplica ponderaciones multicriterio y ejecuta las reglas de negocio RN-01 a RN-08.
=============================================================================
"""

import copy
from typing import List, Dict, Any, Tuple


# =============================================================================
# CONSTANTES DE PONDERACIÓN Y NORMALIZACIÓN
# =============================================================================
PESO_GRAVEDAD = 0.35   # 35% Gravedad del incidente (impacto en seguridad/salud)
PESO_POBLACION = 0.30  # 30% Población directamente afectada
PESO_TIEMPO = 0.20     # 20% Días acumulados sin atención
PESO_RECURSOS = 0.15   # 15% Recursos necesarios (factibilidad de ejecución)

# Escalas de normalización
MAX_GRAVEDAD = 5.0
MAX_POBLACION = 5000.0
MAX_TIEMPO_DIAS = 60.0

# Valoración de recursos (menor recurso = mayor facilidad y retorno rápido)
MAPA_RECURSOS = {
    "Bajo": 100.0,   # Rápida solución, bajo costo operativo (quick-win)
    "Medio": 60.0,   # Requiere cuadrilla estándar y presupuesto medio
    "Alto": 30.0     # Requiere maquinaria pesada, licitación o presupuesto alto
}


def normalizar_factores(reporte: Dict[str, Any]) -> Dict[str, float]:
    """
    Normaliza los cuatro factores clave a una escala uniforme de 0 a 100.
    """
    gravedad = float(reporte.get("gravedad", 1))
    poblacion = float(reporte.get("poblacion_afectada", 10))
    tiempo = float(reporte.get("tiempo_sin_resolver", 1))
    recursos_str = reporte.get("recursos_requeridos", "Medio")

    # Normalización lineal acotada
    norm_gravedad = min(100.0, max(0.0, (gravedad / MAX_GRAVEDAD) * 100.0))
    norm_poblacion = min(100.0, max(0.0, (poblacion / MAX_POBLACION) * 100.0))
    norm_tiempo = min(100.0, max(0.0, (tiempo / MAX_TIEMPO_DIAS) * 100.0))
    norm_recursos = MAPA_RECURSOS.get(recursos_str, 60.0)

    return {
        "norm_gravedad": round(norm_gravedad, 2),
        "norm_poblacion": round(norm_poblacion, 2),
        "norm_tiempo": round(norm_tiempo, 2),
        "norm_recursos": round(norm_recursos, 2)
    }


def consolidar_duplicados(reportes: List[Dict[str, Any]]) -> Dict[Tuple[str, str, str], List[int]]:
    """
    Función que analiza y agrupa reportes por coincidencia de (distrito, zona, categoría).
    Permite detectar concentración de reclamos ciudadanos sobre una misma problemática.
    Retorna un diccionario con la clave (distrito, zona, categoría) y lista de IDs asociados.
    """
    grupos: Dict[Tuple[str, str, str], List[int]] = {}
    for rep in reportes:
        clave = (
            rep.get("distrito", "").strip(),
            rep.get("zona", "").strip(),
            rep.get("categoria", "").strip()
        )
        if clave not in grupos:
            grupos[clave] = []
        grupos[clave].append(rep.get("id"))
    return grupos


def contar_concentracion_zonal(reportes: List[Dict[str, Any]]) -> Dict[Tuple[str, str], int]:
    """
    Calcula cuántos reportes activos existen por combinación de (distrito, zona).
    """
    conteo: Dict[Tuple[str, str], int] = {}
    for rep in reportes:
        if rep.get("estado") != "Resuelto":
            clave = (rep.get("distrito", "").strip(), rep.get("zona", "").strip())
            conteo[clave] = conteo.get(clave, 0) + 1
    return conteo


def calcular_ranking(reportes: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Calcula el ranking de priorización inteligente para la lista de reportes:
    1. Normaliza los 4 factores (gravedad, población, tiempo, recursos) a escala 0-100.
    2. Aplica la ponderación multicriterio: 35%, 30%, 20%, 15%.
    3. Aplica las 8 reglas de negocio (RN-01 a RN-08).
    4. Acota el puntaje a [0, 100] y clasifica en Crítica, Alta, Media, Baja.
    5. Ordena de mayor a menor puntaje.
    """
    if not reportes:
        return []

    # Pre-cálculo para reglas contextuales
    conteo_zonal = contar_concentracion_zonal(reportes)
    grupos_duplicados = consolidar_duplicados(reportes)

    reportes_procesados = []

    for item in reportes:
        rep = copy.deepcopy(item)
        factores = normalizar_factores(rep)
        rep.update(factores)

        # Cálculo de puntaje base ponderado
        p_gravedad = factores["norm_gravedad"] * PESO_GRAVEDAD
        p_poblacion = factores["norm_poblacion"] * PESO_POBLACION
        p_tiempo = factores["norm_tiempo"] * PESO_TIEMPO
        p_recursos = factores["norm_recursos"] * PESO_RECURSOS

        puntaje_base = p_gravedad + p_poblacion + p_tiempo + p_recursos
        puntaje_final = puntaje_base
        reglas_aplicadas = []

        # =====================================================================
        # APLICACIÓN DE REGLAS DE NEGOCIO (RN-01 a RN-08)
        # =====================================================================
        clave_zona = (rep.get("distrito", "").strip(), rep.get("zona", "").strip())
        clave_dup = (
            rep.get("distrito", "").strip(),
            rep.get("zona", "").strip(),
            rep.get("categoria", "").strip()
        )

        es_resuelto = rep.get("estado") == "Resuelto"

        if not es_resuelto:
            # RN-01: Concentración Zonal (3 o más reportes activos en la misma zona)
            if conteo_zonal.get(clave_zona, 0) >= 3:
                bono_zonal = 7.0
                puntaje_final += bono_zonal
                reglas_aplicadas.append({
                    "codigo": "RN-01",
                    "nombre": "Concentración Zonal",
                    "impacto": f"+{bono_zonal} pts",
                    "detalle": f"Foco crítico detectado: {conteo_zonal.get(clave_zona)} reportes en {rep.get('distrito')} ({rep.get('zona')})."
                })

            # RN-02: Detección de Duplicados / Reportes Reincidentes
            coincidentes = grupos_duplicados.get(clave_dup, [])
            if len(coincidentes) > 1:
                bono_dup = 5.0
                puntaje_final += bono_dup
                reglas_aplicadas.append({
                    "codigo": "RN-02",
                    "nombre": "Reincidencia / Duplicados",
                    "impacto": f"+{bono_dup} pts",
                    "detalle": f"Existe coincidencia vecinal con {len(coincidentes)} reportes similares en la misma zona."
                })

            # RN-03: Antigüedad Crítica (> 30 días sin resolver)
            dias = int(rep.get("tiempo_sin_resolver", 0))
            if dias > 30:
                bono_antiguedad = 8.0
                puntaje_final += bono_antiguedad
                reglas_aplicadas.append({
                    "codigo": "RN-03",
                    "nombre": "Antigüedad Crítica",
                    "impacto": f"+{bono_antiguedad} pts",
                    "detalle": f"El problema acumula {dias} días sin resolverse (supera el umbral de 30 días)."
                })

            # RN-04: Optimización de Recursos (Quick-Wins de impacto rápido)
            if rep.get("recursos_requeridos") == "Bajo":
                bono_quickwin = 4.0
                puntaje_final += bono_quickwin
                reglas_aplicadas.append({
                    "codigo": "RN-04",
                    "nombre": "Optimización de Recursos",
                    "impacto": f"+{bono_quickwin} pts",
                    "detalle": "Resolución de bajo costo y alta factibilidad técnica para despacho inmediato."
                })

            # RN-05: Umbral de Riesgo Extremo
            gravedad_val = int(rep.get("gravedad", 1))
            poblacion_val = int(rep.get("poblacion_afectada", 0))
            categoria_val = rep.get("categoria", "")

            es_emergencia = (gravedad_val == 5 and poblacion_val >= 1000) or (
                categoria_val in ["Inundaciones", "Fugas de Agua"] and gravedad_val == 5
            )

            if es_emergencia:
                if puntaje_final < 85.0:
                    puntaje_final = max(puntaje_final, 85.0)
                    impacto_str = "Fijado en mínimo 85 pts"
                else:
                    puntaje_final += 5.0
                    impacto_str = "+5.0 pts (Emergencia)"

                reglas_aplicadas.append({
                    "codigo": "RN-05",
                    "nombre": "Umbral de Riesgo Extremo",
                    "impacto": impacto_str,
                    "detalle": "Incidencia de severidad máxima que compromete la seguridad de más de 1,000 personas o servicios vitales."
                })

            # RN-06: Límites de Puntaje (Clamping estricto en [0.0, 100.0])
            puntaje_acotado = max(0.0, min(100.0, puntaje_final))
            if puntaje_final != puntaje_acotado:
                reglas_aplicadas.append({
                    "codigo": "RN-06",
                    "nombre": "Límites de Puntaje",
                    "impacto": "Acotado [0-100]",
                    "detalle": "Puntaje ajustado al rango matemático permitido de 0 a 100."
                })
            puntaje_final = puntaje_acotado

            # RN-07: Clasificación por Rangos
            if puntaje_final >= 80.0:
                clasificacion = "Crítica"
            elif puntaje_final >= 65.0:
                clasificacion = "Alta"
            elif puntaje_final >= 45.0:
                clasificacion = "Media"
            else:
                clasificacion = "Baja"

            reglas_aplicadas.append({
                "codigo": "RN-07",
                "nombre": "Clasificación por Rango",
                "impacto": clasificacion,
                "detalle": f"Puntaje de {round(puntaje_final, 1)} pts asignado al segmento {clasificacion}."
            })

        else:
            # RN-08: Gestión de Casos Resueltos
            puntaje_final = 0.0
            clasificacion = "Baja"
            reglas_aplicadas.append({
                "codigo": "RN-08",
                "nombre": "Caso Resuelto",
                "impacto": "0 pts (Inactivo)",
                "detalle": "El reporte ya fue atendido y resuelto. Pasa a histórico sin consumir prioridad activa."
            })

        rep["puntaje_base"] = round(puntaje_base, 2)
        rep["puntaje"] = round(puntaje_final, 2)
        rep["clasificacion"] = clasificacion
        rep["reglas_aplicadas"] = reglas_aplicadas
        rep["desglose_ponderado"] = {
            "gravedad_pts": round(p_gravedad, 2),
            "poblacion_pts": round(p_poblacion, 2),
            "tiempo_pts": round(p_tiempo, 2),
            "recursos_pts": round(p_recursos, 2)
        }
        rep["explicacion"] = generar_explicacion(rep)

        reportes_procesados.append(rep)

    # Ordenar ranking de mayor a menor puntaje (los activos primero, resueltos al final)
    reportes_procesados.sort(key=lambda r: (r["puntaje"], r["gravedad"], r["poblacion_afectada"]), reverse=True)

    # Asignar posición de ranking correlativa
    for index, rep in enumerate(reportes_procesados, start=1):
        rep["ranking_posicion"] = index

    return reportes_procesados


def generar_explicacion(reporte: Dict[str, Any]) -> str:
    """
    Genera un informe explicativo legible y técnico justificando el puntaje
    calculado por el motor de IA para el reporte específico.
    """
    if reporte.get("estado") == "Resuelto":
        return (
            "Este reporte se encuentra en estado 'Resuelto'. Conforme a la regla de negocio RN-08, "
            "la incidencia ya ha recibido intervención operativa y no requiere asignación de nuevos recursos, "
            "por lo que su puntaje de prioridad activa se ajusta a 0.0 puntos para archivar su histórico."
        )

    puntaje = reporte.get("puntaje", 0.0)
    clasificacion = reporte.get("clasificacion", "Baja")
    gravedad = reporte.get("gravedad", 1)
    poblacion = reporte.get("poblacion_afectada", 0)
    tiempo = reporte.get("tiempo_sin_resolver", 0)
    recursos = reporte.get("recursos_requeridos", "Medio")
    categoria = reporte.get("categoria", "Incidencia")
    distrito = reporte.get("distrito", "el distrito")
    zona = reporte.get("zona", "la zona")

    desglose = reporte.get("desglose_ponderado", {})
    p_grav = desglose.get("gravedad_pts", 0.0)
    p_pob = desglose.get("poblacion_pts", 0.0)
    p_tiempo = desglose.get("tiempo_pts", 0.0)
    p_rec = desglose.get("recursos_pts", 0.0)

    # Identificar el factor determinante
    factores_dict = {
        "Gravedad": p_grav,
        "Población": p_pob,
        "Tiempo de Espera": p_tiempo,
        "Viabilidad de Recursos": p_rec
    }
    factor_mayor = max(factores_dict, key=factores_dict.get)

    reglas = reporte.get("reglas_aplicadas", [])
    codigos_reglas = [r["codigo"] for r in reglas if r["codigo"] in ["RN-01", "RN-02", "RN-03", "RN-04", "RN-05"]]
    str_reglas = ", ".join(codigos_reglas) if codigos_reglas else "Ninguna bonificación extraordinaria"

    explicacion = (
        f"El reporte de {categoria} en {distrito} (Zona {zona}) ha sido clasificado con Prioridad {clasificacion.upper()} "
        f"con un puntaje final de {puntaje} / 100 puntos. "
        f"El factor más influyente en su evaluación multicriterio fue '{factor_mayor}'. "
        f"Evaluación específica: Gravedad nivel {gravedad}/5 ({p_grav} pts ponderados), "
        f"impacto directo sobre {poblacion:,} ciudadanos ({p_pob} pts), "
        f"tiempo de espera acumulado de {tiempo} días ({p_tiempo} pts) y requerimiento de recursos '{recursos}' ({p_rec} pts). "
    )

    if codigos_reglas:
        explicacion += f"Adicionalmente, el motor de IA activó las reglas de negocio especiales ({str_reglas}), "
        detalles_reglas = [f"{r['codigo']} ({r['nombre']}: {r['impacto']})" for r in reglas if r["codigo"] in codigos_reglas]
        explicacion += f"incluyendo: {'; '.join(detalles_reglas)}, consolidando su posición en la cuadrilla municipal."
    else:
        explicacion += "No se registraron bonificaciones por emergencias extremas ni reincidencia zonal múltiple."

    return explicacion
