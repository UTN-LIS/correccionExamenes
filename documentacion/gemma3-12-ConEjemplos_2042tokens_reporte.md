# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `gemma3-12-ConEjemplos_2042tokens.csv`  
**Fecha de análisis:** lun 08 jun 2026 13:56:43 -03  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** 76
- **Filas procesadas correctamente:** 4 (5.3%)
- **Filas fallidas (sin nota parseable):** 72 (94.7%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `2.00` | `2.00` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `1.00` | `1.00` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `0.00` | `0.00` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `50.0%` | `50.0%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `50.0%` | `50.0%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-2** | 1 | 25.0% | `█████` |
| **0** | 2 | 50.0% | `██████████` |
| **+2** | 1 | 25.0% | `█████` |

### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **-2** | 1 | 25.0% | `█████` |
| **0** | 2 | 50.0% | `██████████` |
| **+2** | 1 | 25.0% | `█████` |

---

## ⚠️ Filas no Parseables (Fallas de Extracción)
Los siguientes pasos (72) no contenían una nota numérica identificable en la columna de salida:

- **Paso 0**: Esperado: `4.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre aserciones en pruebas de software. La compararé con lo q...*
- **Paso 1**: Esperado: `2.0` | Salida (resumen): *Okay, vamos a analizar y corregir esta respuesta sobre aserciones en software.

**Análisis de la Res...*
- **Paso 2**: Esperado: `5.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta desde la perspectiva de un profesor experto en evaluación acad...*
- **Paso 3**: Esperado: `4.0` | Salida (resumen): *¡Absolutamente! Vamos a analizar esta respuesta como si fuera un trabajo de un estudiante sobre "Ase...*
- **Paso 4**: Esperado: `6.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre aserciones en el contexto de pruebas de software.

**Aná...*
- **Paso 5**: Esperado: `6.0` | Salida (resumen): *## Corrección de la Respuesta sobre "Assertions"

**Análisis de la Respuesta:**

La respuesta del es...*
- **Paso 6**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar la respuesta del estudiante.

**Análisis de la Respuesta:**

La respuesta abo...*
- **Paso 7**: Esperado: `5.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta desde la perspectiva de un profesor experto en evaluación acad...*
- **Paso 8**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre "assertions" en el contexto de pruebas de software (asum...*
- **Paso 9**: Esperado: `6.0` | Salida (resumen): *Okay, voy a analizar y corregir esta respuesta sobre aserciones (assertions) en programación. A cont...*
- **Paso 10**: Esperado: `6.0` | Salida (resumen): *Okay, vamos a analizar la respuesta del estudiante sobre la función de las aserciones en las pruebas...*
- **Paso 12**: Esperado: `8.0` | Salida (resumen): *## Corrección de la Respuesta del Estudiante sobre Aserciones en Test

**Análisis:**

La respuesta d...*
- **Paso 13**: Esperado: `5.0` | Salida (resumen): *Okay, analicemos la respuesta del estudiante "Los assert sirven para comprobar lo que devuelve o hac...*
- **Paso 14**: Esperado: `7.0` | Salida (resumen): *Okay, analicemos esta respuesta sobre las aserciones en pruebas (tests).

**Corrección y Análisis:**...*
- **Paso 15**: Esperado: `2.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre el uso de aserciones en pruebas de software.

**Análisis...*
- **Paso 16**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar la respuesta del estudiante sobre las aserciones (assertions) en programación...*
- **Paso 17**: Esperado: `9.0` | Salida (resumen): *Okay, analicemos esta respuesta sobre "aserción" en el contexto de pruebas unitarias. A continuación...*
- **Paso 18**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre el uso de aserciones y excepciones, comparándola con eje...*
- **Paso 19**: Esperado: `0.0` | Salida (resumen): *Okay, analicemos esta respuesta. Para hacer esto de manera efectiva, necesito saber el contexto de l...*
- **Paso 20**: Esperado: `8.0` | Salida (resumen): *Okay, analicemos esta respuesta y la calificaremos.

**Análisis de la Respuesta:**

La respuesta es ...*
- **Paso 21**: Esperado: `4.0` | Salida (resumen): *Okay, vamos a analizar la respuesta del estudiante sobre los tests, comparándola con ejemplos de cor...*
- **Paso 22**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre las aserciones en pruebas (testing).

**Análisis de la R...*
- **Paso 23**: Esperado: `1.0` | Salida (resumen): *Okay, analicemos esta respuesta desde la perspectiva de un profesor experto en evaluación académica,...*
- **Paso 25**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar la respuesta del estudiante y evaluarla como si fuera una corrección académic...*
- **Paso 26**: Esperado: `7.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta a la pregunta (que no se ha proporcionado, pero asumimos que t...*
- **Paso 27**: Esperado: `4.0` | Salida (resumen): *Okay, analicemos esta respuesta como si fuera la de un estudiante en un contexto de evaluación acadé...*
- **Paso 28**: Esperado: `4.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta y compararla con ejemplos de correcciones reales que he visto ...*
- **Paso 29**: Esperado: `3.0` | Salida (resumen): *Okay, voy a analizar la respuesta del estudiante sobre las aseveraciones en la evaluación y proporci...*
- **Paso 30**: Esperado: `9.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta y corregirla, comparándola con lo que esperaría de un estudian...*
- **Paso 31**: Esperado: `8.0` | Salida (resumen): *Okay, vamos a analizar esta respuesta sobre aserciones en tests.

**Análisis de la Respuesta:**

La ...*

*... y 42 filas más no parseables.*