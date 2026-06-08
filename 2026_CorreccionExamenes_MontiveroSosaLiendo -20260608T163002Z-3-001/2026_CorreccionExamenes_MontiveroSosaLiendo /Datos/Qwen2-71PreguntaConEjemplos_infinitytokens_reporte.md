# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `Qwen2-71PreguntaConEjemplos_infinitytokens.csv`  
**Fecha de análisis:** lun 08 jun 2026 13:40:29 -03  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** 80
- **Filas procesadas correctamente:** 77 (96.2%)
- **Filas fallidas (sin nota parseable):** 3 (3.8%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `4.00` | `4.00` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `1.53` | `1.53` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `-0.82` | `-0.82` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `18.2%` | `18.2%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `55.8%` | `55.8%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-3** | 2 | 2.6% | `█` |
| **-2** | 6 | 7.8% | `██` |
| **-1** | 9 | 11.7% | `██` |
| **0** | 15 | 19.5% | `████` |
| **+1** | 19 | 24.7% | `█████` |
| **+2** | 12 | 15.6% | `███` |
| **+3** | 9 | 11.7% | `██` |
| **+4** | 5 | 6.5% | `█` |

### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-3** | 2 | 2.6% | `█` |
| **-2** | 6 | 7.8% | `██` |
| **-1** | 9 | 11.7% | `██` |
| **0** | 15 | 19.5% | `████` |
| **+1** | 19 | 24.7% | `█████` |
| **+2** | 12 | 15.6% | `███` |
| **+3** | 9 | 11.7% | `██` |
| **+4** | 5 | 6.5% | `█` |

---

## ⚠️ Filas no Parseables (Fallas de Extracción)
Los siguientes pasos (3) no contenían una nota numérica identificable en la columna de salida:

- **Paso 5**: Esperado: `6.0` | Salida (resumen): *{'response': 'respuesta no obtenida'}*
- **Paso 18**: Esperado: `7.0` | Salida (resumen): *{'response': 'respuesta no obtenida'}*
- **Paso 76**: Esperado: `6.0` | Salida (resumen): *{'response': 'respuesta no obtenida'}*
