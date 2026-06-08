# Manual de Uso: Cálculo Automatizado de Métricas de Evaluación

Este documento describe el funcionamiento y uso del script `procesar_metricas.py`, diseñado para extraer calificaciones de los exámenes corregidos por modelos de lenguaje (LLM) a partir de archivos de experimentos en formato CSV, y calcular automáticamente las métricas de rendimiento y desviación frente a las calificaciones reales de los profesores.

---

## 🚀 Cómo Ejecutar el Script

El script soporta dos modos de funcionamiento:

### Modo 1: Selección Interactiva (Recomendado)
Si ejecutas el script sin argumentos, este escaneará automáticamente el directorio actual y sus subcarpetas para buscar archivos `.csv` válidos (excluyendo los que ya fueron procesados) y te mostrará una lista interactiva para que selecciones cuál deseas procesar:

```bash
python3 procesar_metricas.py
```

*Ejemplo de salida:*
```text
Buscador de Experimentos CSV
Seleccione el archivo que desea procesar ingresando su número:
  [0] 2026_CorreccionExamenes_MontiveroSosaLiendo/Datos/resultados.csv
  [1] 2026_CorreccionExamenes_MontiveroSosaLiendo/Datos/Qwen2-71PreguntaConEjemplos_infinitytokens.csv

Selección (número): 
```

### Modo 2: Argumento Directo por Consola
Puedes especificar la ruta del archivo CSV directamente al ejecutar el comando:

```bash
python3 procesar_metricas.py "./2026_CorreccionExamenes_MontiveroSosaLiendo/Datos/resultados.csv"
```

---

## ⚙️ Integración Automática en el Experimento
El script se encuentra integrado en el flujo de ejecución principal en `main.py`. Cuando ejecutas un nuevo experimento con:

```bash
python3 main.py
```

Al finalizar la corrección del dataset por parte del LLM, el sistema invocará automáticamente a `procesar_metricas.py` sobre el archivo de resultados configurado en tu `.env` (generalmente `resultados.csv`). De esta forma, **las métricas y los archivos procesados se generarán sin que tengas que ejecutar nada de forma manual**.

---

## 📊 Archivos Generados

Al procesar un archivo `mi_experimento.csv`, el script generará dos archivos nuevos en la misma carpeta:

1. **`mi_experimento_procesado.csv`**: Una copia del CSV original con 7 nuevas columnas añadidas para cada fila:
   - `nota_modelo`: La nota numérica cruda extraída del texto del LLM.
   - `denominador_modelo`: El denominador de la nota si se detectó una fracción (ej. `5` si decía `3 de 5`).
   - `nota_modelo_normalizada`: La nota escalada a base 10 (ej. `3 de 5` pasa a ser `6.00`).
   - `diferencia`: Diferencia cruda (`esperado - nota_modelo`).
   - `diferencia_absoluta`: Valor absoluto de la diferencia cruda.
   - `diferencia_normalizada`: Diferencia utilizando la nota normalizada (`esperado - nota_modelo_normalizada`).
   - `diferencia_absoluta_normalizada`: Valor absoluto de la diferencia normalizada.

2. **`mi_experimento_reporte.md`**: Un reporte detallado en Markdown que incluye resúmenes de rendimiento, histogramas visuales de desviaciones y un listado de filas en las que no se pudo extraer una nota (para facilitar la depuración de respuestas incompletas o bloqueadas del LLM).

---

## 🔍 Reglas de Extracción de Notas (Robustez de Formatos)

El extractor implementado utiliza expresiones regulares en cascada y análisis multilínea para manejar la inconsistencia de respuestas del LLM. Sigue esta prioridad de búsqueda:

1. **Patrón Fraccionario con Palabra Clave**: Busca palabras clave como `Nota`, `Calificación`, `Puntaje` o `Puntuación`, seguidas de separadores (`:`, `**`, etc.) y una fracción como `X/Y` o `X de Y` (ej: `Calificación: 8/10`, `Puntaje: 3 de 5`).
2. **Patrón Simple con Palabra Clave**: Busca las mismas palabras clave seguidas de un único número entero o decimal (ej: `Nota: 4`, `calificacion : 9.5`).
3. **Filtro de Texto Corto**: Si el texto de salida es muy corto (menos de 20 caracteres) y contiene un número o fracción, lo extrae directamente (ej. para salidas crudas como `7<|eot_id|>` o `8.5`).
4. **Búsqueda Aislada Multilínea**: Si el LLM escribe una justificación larga y luego coloca la nota sola en un párrafo al final, el script busca si hay líneas completas formadas únicamente por un número o fracción.

> Si una fila contiene errores de API (ej. `{'response': 'respuesta no obtenida'}`) o el modelo no generó una calificación por bloqueo de seguridad, el script marca dicha fila como **"Falla de Extracción"**, excluyéndola de los cálculos matemáticos para no sesgar las métricas de precisión, pero reportándola en el listado de fallos para su revisión.

---

## 📈 Explicación de las Métricas Calculadas

El reporte de salida genera dos tablas comparativas: **Notas Raw** (comparación directa con los valores extraídos) y **Notas Normalizadas** (escaladas a base 10 si tenían denominador distinto a 10). Las métricas son:

### 1. Error Máximo (Max Error)
Representa la desviación más grande que tuvo el modelo en todo el experimento frente al profesor.
$$\text{Error Máximo} = \max | \text{Esperado}_i - \text{Modelo}_i |$$
* **Interpretación**: Muestra el "peor caso" del modelo. Si el error máximo es alto (ej. 6.0 puntos), indica que al menos en un examen el modelo tuvo una discrepancia muy grave.

### 2. Error Medio Absoluto (MAE - Mean Absolute Error)
Es el promedio de la distancia absoluta entre las notas esperadas y las del modelo.
$$\text{MAE} = \frac{1}{N} \sum_{i=1}^{N} | \text{Esperado}_i - \text{Modelo}_i |$$
* **Interpretación**: Es la métrica principal de precisión. Un MAE de `1.45` significa que, en promedio, las calificaciones del modelo se desvían $\pm 1.45$ puntos de la calificación real del profesor. Cuanto más cercano a 0, mejor.

### 3. Sesgo del Cálculo (Bias)
Mide la dirección promedio del error (si el modelo tiende a sobrecalificar o subcalificar). Se calcula como la media de la diferencia firmada:
$$\text{Sesgo} = \frac{1}{N} \sum_{i=1}^{N} (\text{Modelo}_i - \text{Esperado}_i)$$
* **Interpretación**: 
  * Un sesgo **positivo** (ej. `+0.5`) indica que el modelo es "benevolente" y tiende a poner notas más altas que el profesor en promedio.
  * Un sesgo **negativo** (ej. `-0.8`) indica que el modelo es "estricto" y tiende a calificar por debajo del profesor.
  * Un sesgo cercano a `0.0` indica que el modelo no tiene una desviación sistemática en ninguna dirección.

### 4. Coincidencia Exacta (Exact Match)
Porcentaje de casos en los que la nota del modelo fue exactamente igual a la del profesor (Diferencia = 0).
* **Interpretación**: Porcentaje de aciertos perfectos de la IA.

### 5. Coincidencia a ±1 Punto
Porcentaje de casos en los que la nota de la IA difiere en un punto o menos de la del profesor ($| \text{Esperado} - \text{Modelo} | \le 1.0$).
* **Interpretación**: Tolerancia aceptable. En pedagogía, una diferencia de hasta 1 punto suele considerarse dentro del rango de variación subjetiva entre correctores humanos.

### 6. Distribución de Diferencias (Histograma)
Muestra cuántas veces ocurrió cada nivel de diferencia discreta ($\text{Esperado} - \text{Modelo}$).
* **Diferencia de `+1`**: El profesor puso un punto más que la IA (IA subcalificó).
* **Diferencia de `-2`**: El profesor puso dos puntos menos que la IA (IA sobrecalificó).
* **Interpretación**: Permite visualizar la campana de Gauss del error del modelo para detectar si el error está bien concentrado en torno al 0 (lo ideal) o si está disperso.
