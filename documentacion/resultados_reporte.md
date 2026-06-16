# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `resultados.csv`  
**Fecha de análisis:** La fecha actual es: s b 13/06/2026 
Escriba la nueva fecha: (dd-mm-aa)  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** 303
- **Filas procesadas correctamente:** 1 (0.3%)
- **Filas fallidas (sin nota parseable):** 302 (99.7%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `1.00` | `1.00` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `1.00` | `1.00` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `-1.00` | `-1.00` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `0.0%` | `0.0%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `100.0%` | `100.0%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **+1** | 1 | 100.0% | `████████████████████` |

### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
| **+1** | 1 | 100.0% | `████████████████████` |

---

## ⚠️ Filas no Parseables (Fallas de Extracción)
Los siguientes pasos (302) no contenían una nota numérica identificable en la columna de salida:

- **Paso 0**: Esperado: `9.0` | Salida (resumen): *El TDD en inglés es Test-Driven Development, es un mecanismo de test independientes para el proceso ...*
- **Paso 1**: Esperado: `7.0` | Salida (resumen): *El TDD nos ayuda a comprobar que la implementación de los métodos de la práctica y su uso sean corre...*
- **Paso 2**: Esperado: `6.0` | Salida (resumen): *Las buenas prácticas del TDD son: 

* El código de cada test tiene que ser independiente de cada uno...*
- **Paso 3**: Esperado: `7.0` | Salida (resumen): *La importancia de validar las entradas en el TDD es necesaria ya que implementa el código con datos ...*
- **Paso 4**: Esperado: `8.0` | Salida (resumen): *Es una metodología en el desarrolo de proyectos software que se divide en fases, la fase en rojo nos...*
- **Paso 5**: Esperado: `6.0` | Salida (resumen): *El Test Driven Development nos permite probar paso a paso durante el ciclo del desarrolo software a ...*
- **Paso 6**: Esperado: `8.0` | Salida (resumen): *Las buenas practicas del Test Driven Development serian el hecho de realizar test de cobertura que d...*
- **Paso 7**: Esperado: `7.0` | Salida (resumen): *Es importante validar las entradas del Test Driven Development en relacion al contexto, cuanto mas t...*
- **Paso 8**: Esperado: `10.0` | Salida (resumen): *El ciclo TDD (Test-Driven Development) consiste en 3 pasos cíclicos para desarrollar un codigo por c...*
- **Paso 9**: Esperado: `9.0` | Salida (resumen): *El enfoque tradicional de testing era que priemro se desarrollaba el codigo del proyecto y luego se ...*
- **Paso 10**: Esperado: `6.0` | Salida (resumen): *Tenemos diferentes buenas prácticas en TDD:

* Que tengan un nombre descriptivo: es importante que l...*
- **Paso 11**: Esperado: `10.0` | Salida (resumen): *El TDD es una metodologia en la que se crean unos test y posteriormente se programa las funcionalida...*
- **Paso 12**: Esperado: `8.0` | Salida (resumen): *Comparado con el testing tradicional que se basa en primero hacer la programación y luego crear los ...*
- **Paso 13**: Esperado: `6.0` | Salida (resumen): *Entre las buenas practicas destacan sobre todo las siguientes:
- Que tengan un nombre descriptivo, c...*
- **Paso 14**: Esperado: `3.0` | Salida (resumen): *Es muy importante el validar entradas ya que comienzas con una estructura muy robusta y correcta, si...*
- **Paso 15**: Esperado: `9.0` | Salida (resumen): *El ciclo de TDD consiste en un formato de 3 pasos.

El primero consiste en el rojo, que se trata de ...*
- **Paso 16**: Esperado: `6.0` | Salida (resumen): *En el enfoque tradicional de testing en el desarrollo de software es algo que se centra más en el có...*
- **Paso 17**: Esperado: `3.0` | Salida (resumen): *Las buenas prácticas del TDD trata de mejorar el desarrollo de software progresivamente durante el d...*
- **Paso 18**: Esperado: `6.0` | Salida (resumen): *Para validar las entradas en el cotexto de TDD vamos a evitar los casos Edge, se refiere a los casos...*
- **Paso 19**: Esperado: `10.0` | Salida (resumen): *El ciclo TDD (Test Driven Development) es una metodología utilizada en la ingeniería del software qu...*
- **Paso 20**: Esperado: `10.0` | Salida (resumen): *En el TDD se escriben primero los tests y luego el código en base a lo que cubren dichas pruebas, pe...*
- **Paso 21**: Esperado: `9.0` | Salida (resumen): *-El uso del principio FIRST debe utilizarse para crear tests rápidos, independientes, reutilizables ...*
- **Paso 22**: Esperado: `5.0` | Salida (resumen): *Es importante validar entradas en el contexto de TDD puesto que garantiza que el código no devuelva ...*
- **Paso 23**: Esperado: `5.0` | Salida (resumen): *El ciclo TDD (Test Driven Development), se basa en desarrollar aplicaciones siguiendo el ciclo Red -...*
- **Paso 24**: Esperado: `7.0` | Salida (resumen): *En el desarrollo de software, en un ciclo tradicional de testing se busca directamente escribir el c...*
- **Paso 25**: Esperado: `6.0` | Salida (resumen): *Una buena práctica del TDD es la nomenclatura, es decir, que los tests tengan un nombre que represen...*
- **Paso 26**: Esperado: `4.0` | Salida (resumen): *La validación de entradas en los ciclos TDD es importante ya que te encargas de que las entradas exi...*
- **Paso 27**: Esperado: `8.0` | Salida (resumen): *El ciclo TDD es una metodología de desarrollo la cual sigue 3 pasos, el paso red, el primero, se rea...*
- **Paso 28**: Esperado: `6.0` | Salida (resumen): *El mecanismo TDD se ejecutan pruebas y luego se escribe el código, mientras que el enfoque tradicion...*
- **Paso 29**: Esperado: `6.0` | Salida (resumen): *poner nombres simples e intuitivos, seguir el enfoque de las tres AAA y no probar varias funcionalid...*

*... y 272 filas más no parseables.*