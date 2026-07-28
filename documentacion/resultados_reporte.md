# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `resultados.csv`  
**Fecha de análisis:** lun 27 jul 2026 21:54:36 -03  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** 3
- **Filas procesadas correctamente:** 3 (100.0%)
- **Filas fallidas (sin nota parseable):** 0 (0.0%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `2.00` | `2.00` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `1.33` | `1.33` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `0.67` | `0.67` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `0.0%` | `0.0%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `66.7%` | `66.7%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-2** | 1 | 33.3% | `███████` |
| **-1** | 1 | 33.3% | `███████` |
| **+1** | 1 | 33.3% | `███████` |

### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-2** | 1 | 33.3% | `███████` |
| **-1** | 1 | 33.3% | `███████` |
| **+1** | 1 | 33.3% | `███████` |
