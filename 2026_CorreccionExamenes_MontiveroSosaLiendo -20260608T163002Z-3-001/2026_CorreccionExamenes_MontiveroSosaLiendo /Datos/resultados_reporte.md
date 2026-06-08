# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `resultados.csv`  
**Fecha de análisis:** lun 08 jun 2026 13:39:42 -03  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** 150
- **Filas procesadas correctamente:** 108 (72.0%)
- **Filas fallidas (sin nota parseable):** 42 (28.0%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `6.00` | `6.00` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `1.85` | `1.45` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `-1.23` | `-0.35` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `10.2%` | `12.0%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `49.1%` | `62.0%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-4** | 1 | 0.9% | `▏` |
| **-3** | 6 | 5.6% | `█` |
| **-2** | 5 | 4.6% | `█` |
| **-1** | 27 | 25.0% | `█████` |
| **0** | 15 | 13.9% | `███` |
| **+1** | 25 | 23.1% | `█████` |
| **+2** | 20 | 18.5% | `████` |
| **+3** | 6 | 5.6% | `█` |
| **+4** | 2 | 1.9% | `▏` |
| **+6** | 1 | 0.9% | `▏` |

### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-4** | 1 | 0.9% | `▏` |
| **-3** | 3 | 2.8% | `█` |
| **-2** | 3 | 2.8% | `█` |
| **-1** | 14 | 13.0% | `███` |
| **0** | 13 | 12.0% | `██` |
| **+1** | 26 | 24.1% | `█████` |
| **+2** | 26 | 24.1% | `█████` |
| **+3** | 11 | 10.2% | `██` |
| **+4** | 4 | 3.7% | `█` |
| **+5** | 3 | 2.8% | `█` |
| **+6** | 4 | 3.7% | `█` |

---

## ⚠️ Filas no Parseables (Fallas de Extracción)
Los siguientes pasos (42) no contenían una nota numérica identificable en la columna de salida:

- **Paso 13**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante contiene algunos elementos correctos, p...*
- **Paso 16**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **parcialmente correcta**, pero **no co...*
- **Paso 17**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **tiene un enfoque generalmente correct...*
- **Paso 18**: Esperado: `2.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 22**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta **elementos relevantes** sobre...*
- **Paso 25**: Esperado: `8.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta una **comprensión parcial** de...*
- **Paso 31**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta un intento válido de describir...*
- **Paso 34**: Esperado: `4.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **presenta un intento de definir el con...*
- **Paso 38**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **es parcialmente correcta y muestra un...*
- **Paso 40**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 42**: Esperado: `8.0` | Salida (resumen): ***Evaluación de la respuesta:**

✅ **Puntos positivos:**

La respuesta del estudiante identifica cor...*
- **Paso 45**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **tiene un inicio prometedor** y mencio...*
- **Paso 46**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta, pero incomp...*
- **Paso 50**: Esperado: `9.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta una visión parcialmente correc...*
- **Paso 51**: Esperado: `9.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 52**: Esperado: `8.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta una discusión básica sobre las...*
- **Paso 59**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta y bien estru...*
- **Paso 61**: Esperado: `2.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **incompleta y errónea en su enfoque...*
- **Paso 62**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante muestra un intento claro y estructurado...*
- **Paso 65**: Esperado: `4.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 69**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **co...*
- **Paso 72**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta algunos puntos relevantes sobr...*
- **Paso 79**: Esperado: `4.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta algunas ideas correctas y rele...*
- **Paso 83**: Esperado: `4.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **parcialmente correcta**, pero **incom...*
- **Paso 85**: Esperado: `4.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 86**: Esperado: `7.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta**, pero **in...*
- **Paso 89**: Esperado: `10.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta y bien estru...*
- **Paso 97**: Esperado: `2.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante es **parcialmente correcta, pero insufi...*
- **Paso 100**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante **muestra un entendimiento básico del T...*
- **Paso 102**: Esperado: `6.0` | Salida (resumen): ***Evaluación de la respuesta:**

La respuesta del estudiante presenta un intento coherente de aborda...*

*... y 12 filas más no parseables.*