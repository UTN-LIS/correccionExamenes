#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Automatización de Métricas de Calificación de Exámenes
Autor: Antigravity Pair Programmer
Propósito: Procesar archivos CSV de experimentos de corrección de exámenes con IA,
           extraer las notas del modelo en diversos formatos, calcular diferencias y
           generar estadísticas de error y sesgo.
"""

import os
import sys
import re
import csv
import math

# Intentar importar rich para una salida de consola interactiva y estética
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import track
    USE_RICH = True
    console = Console()
except ImportError:
    USE_RICH = False

def print_info(msg):
    if USE_RICH:
        console.print(f"[blue]i[/blue] {msg}")
    else:
        print(f"INFO: {msg}")

def print_success(msg):
    if USE_RICH:
        console.print(f"[green]✔[/green] {msg}")
    else:
        print(f"ÉXITO: {msg}")

def print_warning(msg):
    if USE_RICH:
        console.print(f"[yellow]⚠[/yellow] {msg}")
    else:
        print(f"ADVERTENCIA: {msg}")

def print_error(msg):
    if USE_RICH:
        console.print(f"[red]✘[/red] {msg}")
    else:
        print(f"ERROR: {msg}")

def parsear_calificacion(texto):
    """
    Extrae la nota numérica y el denominador (si existe) a partir de la columna 'salida'.
    Soporta múltiples formatos como: 'Nota: 8', 'Calificación: 8/10', 'Puntaje: 3 de 5', etc.
    """
    if not texto:
        return None, None
    
    # Limpiar tokens comunes de LLM y espacios en blanco
    texto_limpio = texto.replace("<|eot_id|>", "").replace("<|im_end|>", "").strip()
    
    # 1. Patrón con fracción/denominador (ej. "Nota: 8/10", "Calificación: 3 de 5")
    patron_fraccion = re.compile(
        r'(?:nota|calificaci[oó]n|puntuaci[oó]n|puntaje|evaluaci[oó]n|score|grade)\b[^\d\n]*(\d+(?:\.\d+)?)\s*(?:\/|de)\s*(\d+)',
        re.IGNORECASE
    )
    match = patron_fraccion.search(texto_limpio)
    if match:
        try:
            val = float(match.group(1))
            den = float(match.group(2))
            return val, den
        except ValueError:
            pass

    # 2. Patrón simple sin denominador (ej. "Nota: 8", "Calificación: 7.5")
    patron_simple = re.compile(
        r'(?:nota|calificaci[oó]n|puntuaci[oó]n|puntaje|evaluaci[oó]n|score|grade)\b[^\d\n]*(\d+(?:\.\d+)?)',
        re.IGNORECASE
    )
    match = patron_simple.search(texto_limpio)
    if match:
        try:
            return float(match.group(1)), None
        except ValueError:
            pass
            
    # 3. Fallback: Si el texto es corto (<=20 caracteres) y contiene números
    if len(texto_limpio) <= 20:
        # Intentar fracción primero
        match_frac = re.match(r'^\s*(\d+(?:\.\d+)?)\s*(?:\/|de)\s*(\d+)', texto_limpio)
        if match_frac:
            try:
                return float(match_frac.group(1)), float(match_frac.group(2))
            except ValueError:
                pass
        
        # Intentar número simple
        match_num = re.match(r'^\s*(\d+(?:\.\d+)?)', texto_limpio)
        if match_num:
            try:
                return float(match_num.group(1)), None
            except ValueError:
                pass

    # 4. Fallback multilínea: Buscar si alguna línea aislada es puramente numérica o fracción
    for linea in texto_limpio.split('\n'):
        linea_limpia = linea.strip()
        match_frac = re.match(r'^(\d+(?:\.\d+)?)\s*(?:\/|de)\s*(\d+)$', linea_limpia)
        if match_frac:
            try:
                return float(match_frac.group(1)), float(match_frac.group(2))
            except ValueError:
                pass
        match_num = re.match(r'^(\d+(?:\.\d+)?)$', linea_limpia)
        if match_num:
            try:
                return float(match_num.group(1)), None
            except ValueError:
                pass
                
    return None, None

def normalizar_nota(nota, den, escala_objetivo=10.0):
    """
    Normaliza la nota a la escala objetivo (por defecto 10.0) si se detecta un denominador.
    """
    if nota is None:
        return None
    if den and den > 0:
        return (nota / den) * escala_objetivo
    return nota

def buscar_archivos_csv(directorio_base="."):
    """Busca archivos CSV y Excel recursivamente en el directorio, excluyendo los ya procesados."""
    archivos = []
    for raiz, _, files in os.walk(directorio_base):
        for f in files:
            if f.startswith("~$"):
                continue
            ext = os.path.splitext(f)[1].lower()
            if ext == ".csv" and not f.endswith("_procesado.csv"):
                archivos.append(os.path.join(raiz, f))
            elif ext in [".xlsx", ".xls"] and not f.endswith("_procesado.xlsx") and not f.endswith("_procesado.xls"):
                archivos.append(os.path.join(raiz, f))
    return sorted(archivos)

def seleccionar_archivo_interactivo():
    """Presenta una lista de archivos CSV/Excel y permite al usuario elegir uno."""
    archivos = buscar_archivos_csv()
    if not archivos:
        print_error("No se encontraron archivos CSV o Excel en el directorio actual.")
        return None
    
    if USE_RICH:
        console.print(Panel.fit("[bold cyan]Buscador de Experimentos (CSV/Excel)[/bold cyan]\n"
                                "Seleccione el archivo que desea procesar ingresando su número:"))
        for idx, ruta in enumerate(archivos):
            console.print(f"  [bold green][{idx}][/bold green] {os.path.relpath(ruta)}")
    else:
        print("Buscador de Experimentos (CSV/Excel):")
        for idx, ruta in enumerate(archivos):
            print(f"  [{idx}] {os.path.relpath(ruta)}")
            
    while True:
        try:
            seleccion = input("\nSelección (número): ").strip()
            idx = int(seleccion)
            if 0 <= idx < len(archivos):
                return archivos[idx]
            else:
                print_error(f"Número inválido. Debe estar entre 0 y {len(archivos)-1}")
        except ValueError:
            print_error("Por favor, ingrese un número válido.")

def detectar_encabezados(fieldnames):
    """Detecta los encabezados adecuados para esperado, salida y step en base a aliases."""
    aliases_esperado = ['esperado', 'teacher_grade', 'grade', 'nota_real', 'nota_esperada', 'target', 'calificacion_real']
    aliases_salida = ['salida', 'model_output', 'response', 'respuesta_modelo', 'model_response', 'output']
    aliases_step = ['step', 'id', 'index', 'nro']
    
    col_esperado = None
    col_salida = None
    col_step = None
    
    for f in fieldnames:
        f_lower = f.lower().strip()
        if f_lower in aliases_esperado and col_esperado is None:
            col_esperado = f
        if f_lower in aliases_salida and col_salida is None:
            col_salida = f
        if f_lower in aliases_step and col_step is None:
            col_step = f
            
    # Fallbacks si no se encuentra coincidencia exacta de alias
    if col_esperado is None:
        for f in fieldnames:
            if 'grade' in f.lower() or 'nota' in f.lower() or 'espera' in f.lower():
                col_esperado = f
                break
    if col_salida is None:
        for f in fieldnames:
            if 'salida' in f.lower() or 'resp' in f.lower() or 'out' in f.lower():
                col_salida = f
                break
                
    # Fallback definitivo: primeras columnas si no se encuentra nada
    if col_esperado is None:
        col_esperado = 'esperado' if 'esperado' in fieldnames else (fieldnames[4] if len(fieldnames) > 4 else None)
    if col_salida is None:
        col_salida = 'salida' if 'salida' in fieldnames else (fieldnames[3] if len(fieldnames) > 3 else None)
    if col_step is None:
        col_step = 'step' if 'step' in fieldnames else fieldnames[0]
        
    return col_step, col_salida, col_esperado

def calcular_metricas(datos):
    """Calcula las métricas solicitadas a partir de una lista de diccionarios de filas válidas."""
    if not datos:
        return {}
        
    n = len(datos)
    
    # Listas para cálculos de notas raw y normalizadas
    diffs_raw = [d['diff_raw'] for d in datos]
    abs_diffs_raw = [d['abs_diff_raw'] for d in datos]
    
    diffs_norm = [d['diff_norm'] for d in datos]
    abs_diffs_norm = [d['abs_diff_norm'] for d in datos]
    
    # 1. Error Máximo
    max_err_raw = max(abs_diffs_raw)
    max_err_norm = max(abs_diffs_norm)
    
    # 2. Error Medio (MAE)
    mae_raw = sum(abs_diffs_raw) / n
    mae_norm = sum(abs_diffs_norm) / n
    
    # 3. Sesgo del cálculo (Bias = Promedio de nota_modelo - esperado)
    # Nota: Si el sesgo es positivo, el modelo sobrecalifica. Si es negativo, subcalifica.
    bias_raw = sum(d['nota_raw'] - d['esperado'] for d in datos) / n
    bias_norm = sum(d['nota_norm'] - d['esperado'] for d in datos) / n
    
    # 4. Coincidencia Exacta (diferencia absoluta == 0)
    # Redondeamos la diferencia a 2 decimales para evitar problemas de coma flotante
    exact_match_raw = sum(1 for d in abs_diffs_raw if round(d, 2) == 0.0) / n * 100
    exact_match_norm = sum(1 for d in abs_diffs_norm if round(d, 2) == 0.0) / n * 100
    
    # 5. Coincidencia por 1 punto de diferencia (diferencia absoluta <= 1)
    match_1_raw = sum(1 for d in abs_diffs_raw if d <= 1.0) / n * 100
    match_1_norm = sum(1 for d in abs_diffs_norm if d <= 1.0) / n * 100
    
    # 6. Distribución de diferencia por valor (agrupados por entero de diferencia)
    # diferencia = esperado - nota_modelo
    dist_raw = {}
    dist_norm = {}
    
    for d in datos:
        # Redondeamos la diferencia al entero más cercano para agrupar en categorías discretas
        val_raw = int(round(d['diff_raw']))
        val_norm = int(round(d['diff_norm']))
        
        dist_raw[val_raw] = dist_raw.get(val_raw, 0) + 1
        dist_norm[val_norm] = dist_norm.get(val_norm, 0) + 1
        
    # Convertir a porcentajes y ordenar
    dist_raw_pct = {k: (v / n * 100) for k, v in sorted(dist_raw.items())}
    dist_norm_pct = {k: (v / n * 100) for k, v in sorted(dist_norm.items())}
    
    # Matriz de Confusión para aprobación (Umbral >= 4.0)
    def cm_stats(key_modelo):
        tp = sum(1 for d in datos if d['esperado'] >= 4.0 and d[key_modelo] >= 4.0)
        fn = sum(1 for d in datos if d['esperado'] >= 4.0 and d[key_modelo] < 4.0)
        fp = sum(1 for d in datos if d['esperado'] < 4.0 and d[key_modelo] >= 4.0)
        tn = sum(1 for d in datos if d['esperado'] < 4.0 and d[key_modelo] < 4.0)
        total = tp + fn + fp + tn
        pct = lambda val: (val / total * 100) if total > 0 else 0.0
        acc = ((tp + tn) / total * 100) if total > 0 else 0.0
        rec = (tp / (tp + fn) * 100) if (tp + fn) > 0 else 0.0
        prec = (tp / (tp + fp) * 100) if (tp + fp) > 0 else 0.0
        f1 = (2 * prec * rec / (prec + rec)) if (prec + rec) > 0 else 0.0
        return {
            'tp': tp, 'tp_pct': pct(tp),
            'fn': fn, 'fn_pct': pct(fn),
            'fp': fp, 'fp_pct': pct(fp),
            'tn': tn, 'tn_pct': pct(tn),
            'accuracy': acc, 'recall': rec, 'precision': prec, 'f1': f1
        }

    return {
        'n': n,
        'raw': {
            'max_error': max_err_raw,
            'mae': mae_raw,
            'bias': bias_raw,
            'exact_match': exact_match_raw,
            'match_within_1': match_1_raw,
            'distribution': dist_raw_pct,
            'distribution_counts': {k: dist_raw[k] for k in sorted(dist_raw.keys())},
            'confusion_matrix': cm_stats('nota_raw')
        },
        'norm': {
            'max_error': max_err_norm,
            'mae': mae_norm,
            'bias': bias_norm,
            'exact_match': exact_match_norm,
            'match_within_1': match_1_norm,
            'distribution': dist_norm_pct,
            'distribution_counts': {k: dist_norm[k] for k in sorted(dist_norm.keys())},
            'confusion_matrix': cm_stats('nota_norm')
        }
    }

def procesar_csv(ruta_csv):
    """Procesa el CSV o Excel de entrada, extrae las notas, calcula las métricas y genera salidas."""
    if not os.path.exists(ruta_csv):
        print_error(f"El archivo '{ruta_csv}' no existe.")
        return
    
    print_info(f"Cargando archivo: [bold]{os.path.basename(ruta_csv)}[/bold]")
    ext = os.path.splitext(ruta_csv)[1].lower()
    
    filas_raw = []
    fieldnames = []
    tipo_archivo = ""
    
    if ext in ['.xlsx', '.xls']:
        tipo_archivo = "Excel"
        try:
            import pandas as pd
        except ImportError:
            print_error(
                "\nPara procesar archivos de Excel (.xlsx/.xls) necesitas instalar pandas y openpyxl.\n"
                "Por favor ejecuta:\n"
                "  pip install pandas openpyxl\n"
                "O alternativamente, guarda tu archivo como un CSV (.csv) e inténtalo de nuevo."
            )
            return
            
        try:
            df = pd.read_excel(ruta_csv)
            fieldnames = list(df.columns)
            for _, row in df.iterrows():
                d = {}
                for col in fieldnames:
                    val = row[col]
                    if pd.isna(val):
                        d[col] = ""
                    else:
                        d[col] = str(val)
                filas_raw.append(d)
        except Exception as e:
            print_error(f"Error al leer el archivo Excel: {e}")
            return
    else:
        # Intentar decodificar con distintos encodings comunes
        encoding_exitoso = None
        encodings_to_try = ['utf-8-sig', 'utf-8', 'latin-1', 'cp1252']
        for enc in encodings_to_try:
            try:
                with open(ruta_csv, mode='r', encoding=enc) as f:
                    reader = csv.DictReader(f)
                    fieldnames = reader.fieldnames
                    if not fieldnames:
                        continue
                    filas_raw = list(reader)
                    encoding_exitoso = enc
                    break
            except Exception:
                continue
                
        if not encoding_exitoso:
            print_error("No se pudo leer el archivo CSV. Verifique el formato y la codificación.")
            return
        tipo_archivo = f"CSV ({encoding_exitoso})"
        
    print_success(f"Archivo cargado correctamente [{tipo_archivo}] ({len(filas_raw)} filas encontradas)")
    
    # Detectar columnas relevantes
    col_step, col_salida, col_esperado = detectar_encabezados(fieldnames)
    
    if not col_salida or not col_esperado:
        print_error(f"No se pudieron identificar las columnas críticas en el archivo.\n"
                    f"Columnas detectadas: {fieldnames}\n"
                    f"Se requiere al menos una columna de salida del modelo y una de nota esperada.")
        return
        
    print_info(f"Columnas asignadas para análisis:")
    print_info(f"  - Identificador (Step): '{col_step}'")
    print_info(f"  - Salida del Modelo:    '{col_salida}'")
    print_info(f"  - Nota Esperada (Real): '{col_esperado}'")
    
    filas_procesadas = []
    datos_calculo = []
    filas_fallidas = []
    
    # Bucle de procesamiento de filas
    iterator = range(len(filas_raw))
    if USE_RICH:
        iterator = track(iterator, description="Procesando respuestas y extrayendo notas...")
        
    for idx in iterator:
        row = filas_raw[idx]
        step_val = row.get(col_step, str(idx))
        salida_val = row.get(col_salida, "")
        esperado_val = row.get(col_esperado, "")
        
        # Intentar convertir esperado a float
        try:
            esperado_float = float(esperado_val)
        except (ValueError, TypeError):
            esperado_float = None
            
        # Parsear nota del modelo
        nota_extraida, den_extraido = parsear_calificacion(salida_val)
        nota_normalizada = normalizar_nota(nota_extraida, den_extraido)
        
        # Inicializar campos adicionales
        nota_modelo_str = str(nota_extraida) if nota_extraida is not None else ""
        den_modelo_str = str(den_extraido) if den_extraido is not None else ""
        nota_norm_str = f"{nota_normalizada:.2f}" if nota_normalizada is not None else ""
        
        diff_raw_str = ""
        abs_diff_raw_str = ""
        diff_norm_str = ""
        abs_diff_norm_str = ""
        
        # Si tenemos tanto la nota real como la extraída, calculamos diferencias
        if esperado_float is not None and nota_extraida is not None:
            # diferencia = esperado - modelo
            diff_raw = esperado_float - nota_extraida
            abs_diff_raw = abs(diff_raw)
            
            diff_norm = esperado_float - nota_normalizada
            abs_diff_norm = abs(diff_norm)
            
            diff_raw_str = f"{diff_raw:.2f}"
            abs_diff_raw_str = f"{abs_diff_raw:.2f}"
            diff_norm_str = f"{diff_norm:.2f}"
            abs_diff_norm_str = f"{abs_diff_norm:.2f}"
            
            # Guardar para cálculo de métricas generales
            datos_calculo.append({
                'step': step_val,
                'esperado': esperado_float,
                'nota_raw': nota_extraida,
                'nota_norm': nota_normalizada,
                'diff_raw': diff_raw,
                'abs_diff_raw': abs_diff_raw,
                'diff_norm': diff_norm,
                'abs_diff_norm': abs_diff_norm
            })
        else:
            filas_fallidas.append({
                'step': step_val,
                'esperado': esperado_val,
                'salida': salida_val[:100] + "..." if len(salida_val) > 100 else salida_val
            })
            
        # Clonar fila original y agregar nuevas columnas
        nueva_fila = row.copy()
        nueva_fila['nota_modelo'] = nota_modelo_str
        nueva_fila['denominador_modelo'] = den_modelo_str
        nueva_fila['nota_modelo_normalizada'] = nota_norm_str
        nueva_fila['diferencia'] = diff_raw_str
        nueva_fila['diferencia_absoluta'] = abs_diff_raw_str
        nueva_fila['diferencia_normalizada'] = diff_norm_str
        nueva_fila['diferencia_absoluta_normalizada'] = abs_diff_norm_str
        
        filas_procesadas.append(nueva_fila)

    # Calcular métricas globales
    metricas = calcular_metricas(datos_calculo)
    
    # Escribir el nuevo archivo procesado
    ruta_dir, nombre_archivo = os.path.split(ruta_csv)
    nombre_base, _ = os.path.splitext(nombre_archivo)
    
    nuevos_encabezados = fieldnames + [
        'nota_modelo', 'denominador_modelo', 'nota_modelo_normalizada',
        'diferencia', 'diferencia_absoluta',
        'diferencia_normalizada', 'diferencia_absoluta_normalizada'
    ]
    
    # Si la entrada era un Excel, intentar guardar como Excel procesado
    guardado_exitoso = False
    if ext in ['.xlsx', '.xls']:
        try:
            import pandas as pd
            ruta_salida = os.path.join(ruta_dir, f"{nombre_base}_procesado.xlsx")
            df_salida = pd.DataFrame(filas_procesadas)
            # Reordenar columnas para que las nuevas estén al final
            df_salida = df_salida[nuevos_encabezados]
            df_salida.to_excel(ruta_salida, index=False)
            print_success(f"Archivo Excel procesado guardado en: [bold]{ruta_salida}[/bold]")
            guardado_exitoso = True
        except Exception as e:
            print_warning(f"No se pudo guardar como Excel ({e}). Guardando como CSV de respaldo...")
            
    if not guardado_exitoso:
        ruta_csv_salida = os.path.join(ruta_dir, f"{nombre_base}_procesado.csv")
        try:
            with open(ruta_csv_salida, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=nuevos_encabezados)
                writer.writeheader()
                writer.writerows(filas_procesadas)
            print_success(f"Archivo procesado guardado en: [bold]{ruta_csv_salida}[/bold]")
        except Exception as e:
            print_error(f"No se pudo escribir el archivo procesado: {e}")
            return

    # Generar Reporte de Métricas en Markdown
    ruta_reporte_md = os.path.join(ruta_dir, f"{nombre_base}_reporte.md")
    generar_archivo_reporte(ruta_reporte_md, nombre_archivo, metricas, len(filas_raw), len(filas_fallidas), filas_fallidas)
    print_success(f"Reporte de métricas detallado guardado en: [bold]{ruta_reporte_md}[/bold]")
    
    # Mostrar resumen en consola
    mostrar_resumen_consola(nombre_archivo, metricas, len(filas_raw), len(filas_fallidas))

def generar_archivo_reporte(ruta_reporte, nombre_original, metricas, total_filas, total_fallidas, filas_fallidas):
    """Genera el contenido del archivo de reporte markdown."""
    
    # Si no hay datos válidos, reporte mínimo
    if not metricas:
        content = f"""# Reporte de Métricas: {nombre_original}

No se encontraron calificaciones válidas extraídas del modelo para calcular métricas.
- Total de filas analizadas: {total_filas}
- Filas que no se pudieron parsear: {total_fallidas}

## Muestras fallidas
"""
        for f in filas_fallidas[:10]:
            content += f"- **Paso {f['step']}**: Esperado: `{f['esperado']}` | Salida: *{f['salida']}*\n"
        
        with open(ruta_reporte, 'w', encoding='utf-8') as f:
            f.write(content)
        return
        
    n_validos = metricas['n']
    
    content = f"""# Reporte de Métricas de Calificación de Exámenes
**Archivo procesado:** `{nombre_original}`  
**Fecha de análisis:** {os.popen('date').read().strip()}  

---

## 📊 Resumen del Procesamiento de Datos
- **Total de filas en experimento:** {total_filas}
- **Filas procesadas correctamente:** {n_validos} ({n_validos/total_filas*100:.1f}%)
- **Filas fallidas (sin nota parseable):** {total_fallidas} ({total_fallidas/total_filas*100:.1f}%)

---

## 📈 Métricas de Rendimiento del Modelo

Presentamos dos conjuntos de métricas:
1. **Métricas con Notas Raw:** Tomando el valor de la nota directamente como fue devuelto (sin normalizar la escala).
2. **Métricas con Notas Normalizadas:** Escalando automáticamente las notas que tenían denominadores (ej. 3 de 5 pasa a ser 6 de 10) para alinearse con la escala del profesor (0-10).

| Métrica | Notas Raw (Directas) | Notas Normalizadas (Escala 10) | Descripción |
| :--- | :---: | :---: | :--- |
| **Error Máximo** | `{metricas['raw']['max_error']:.2f}` | `{metricas['norm']['max_error']:.2f}` | Mayor desviación absoluta respecto al profesor. |
| **Error Medio (MAE)** | `{metricas['raw']['mae']:.2f}` | `{metricas['norm']['mae']:.2f}` | Promedio de las desviaciones absolutas. |
| **Sesgo del cálculo (Bias)** | `{metricas['raw']['bias']:.2f}` | `{metricas['norm']['bias']:.2f}` | Promedio de error con signo. > 0 sobrecalifica, < 0 subcalifica. |
| **Coincidencia Exacta** | `{metricas['raw']['exact_match']:.1f}%` | `{metricas['norm']['exact_match']:.1f}%` | Porcentaje de coincidencias exactas (Diferencia = 0). |
| **Coincidencia ±1 Punto** | `{metricas['raw']['match_within_1']:.1f}%` | `{metricas['norm']['match_within_1']:.1f}%` | Porcentaje de calificaciones que difieren en 1 punto o menos. |

---

## 🎯 Matriz de Confusión de Aprobación (Umbral >= 4.0)

Esta métrica evalúa la capacidad del modelo para clasificar correctamente el estado de aprobación (nota >= 4.0) de los estudiantes.

### Notas Normalizadas (Recomendado)
- **Verdaderos Positivos (TP - Merecía aprobar y aprobó):** {metricas['norm']['confusion_matrix']['tp']} ({metricas['norm']['confusion_matrix']['tp_pct']:.1f}%)
- **Falsos Negativos (FN - Merecía aprobar y desaprobó):** {metricas['norm']['confusion_matrix']['fn']} ({metricas['norm']['confusion_matrix']['fn_pct']:.1f}%)
- **Falsos Positivos (FP - No merecía aprobar y aprobó):** {metricas['norm']['confusion_matrix']['fp']} ({metricas['norm']['confusion_matrix']['fp_pct']:.1f}%)
- **Verdaderos Negativos (TN - No merecía aprobar y desaprobó):** {metricas['norm']['confusion_matrix']['tn']} ({metricas['norm']['confusion_matrix']['tn_pct']:.1f}%)

| Métrica de Clasificación | Notas Raw | Notas Normalizadas |
| :--- | :---: | :---: |
| **Exactitud de Aprobación (Accuracy)** | `{metricas['raw']['confusion_matrix']['accuracy']:.1f}%` | `{metricas['norm']['confusion_matrix']['accuracy']:.1f}%` |
| **Sensibilidad (Recall)** | `{metricas['raw']['confusion_matrix']['recall']:.1f}%` | `{metricas['norm']['confusion_matrix']['recall']:.1f}%` |
| **Precisión (Precision)** | `{metricas['raw']['confusion_matrix']['precision']:.1f}%` | `{metricas['norm']['confusion_matrix']['precision']:.1f}%` |
| **F1-Score** | `{metricas['raw']['confusion_matrix']['f1']:.1f}%` | `{metricas['norm']['confusion_matrix']['f1']:.1f}%` |

---

## 🎯 Distribución de Diferencias (Esperado - Modelo)

Esta métrica responde a: *"¿Con qué frecuencia la calificación difiere por X puntos?"*  
Una diferencia positiva (`+X`) significa que el profesor calificó más alto que la IA (la IA subcalificó).  
Una diferencia negativa (`-X`) significa que la IA calificó más alto que el profesor (la IA sobrecalificó).

### Distribución con Notas Normalizadas (Recomendado)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
"""
    
    # Generar tabla de histograma para normalizado
    for diff, pct in metricas['norm']['distribution'].items():
        count = metricas['norm']['distribution_counts'][diff]
        barras = "█" * int(round(pct / 5)) if pct >= 2.5 else "▏"
        signo = "+" if diff > 0 else ""
        content += f"| **{signo}{diff}** | {count} | {pct:.1f}% | `{barras}` |\n"
        
    content += """
### Distribución con Notas Raw (Valores sin escalar)
| Diferencia (Pts) | Frecuencia (Casos) | Porcentaje (%) | Histograma Visual |
| :---: | :---: | :---: | :--- |
"""
    
    # Generar tabla de histograma para raw
    for diff, pct in metricas['raw']['distribution'].items():
        count = metricas['raw']['distribution_counts'][diff]
        barras = "█" * int(round(pct / 5)) if pct >= 2.5 else "▏"
        signo = "+" if diff > 0 else ""
        content += f"| **{signo}{diff}** | {count} | {pct:.1f}% | `{barras}` |\n"
        
    # Listar filas fallidas si existen
    if total_fallidas > 0:
        content += f"""
---

## ⚠️ Filas no Parseables (Fallas de Extracción)
Los siguientes pasos ({total_fallidas}) no contenían una nota numérica identificable en la columna de salida:

"""
        for f in filas_fallidas[:30]:
            content += f"- **Paso {f['step']}**: Esperado: `{f['esperado']}` | Salida (resumen): *{f['salida']}*\n"
        if len(filas_fallidas) > 30:
            content += f"\n*... y {len(filas_fallidas) - 30} filas más no parseables.*"
            
    with open(ruta_reporte, 'w', encoding='utf-8') as f:
        f.write(content)

def mostrar_resumen_consola(nombre_archivo, metricas, total_filas, total_fallidas):
    """Muestra un resumen estilizado de las métricas en la terminal."""
    if not metricas:
        print_warning("No hay métricas que mostrar (ningún dato pudo ser parseado).")
        return
        
    n_validos = metricas['n']
    
    if USE_RICH:
        # Título principal
        console.print()
        console.print(Panel(
            f"[bold green]MÉTRICAS COMPLETADAS[/bold green]\n"
            f"Archivo: [yellow]{nombre_archivo}[/yellow]\n"
            f"Casos Válidos: {n_validos}/{total_filas} ({n_validos/total_filas*100:.1f}%) | "
            f"No parseados: {total_fallidas} ({total_fallidas/total_filas*100:.1f}%)",
            title="Resultados del Experimento", expand=False
        ))
        
        # Tabla comparativa de métricas
        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("Métrica", style="cyan")
        table.add_column("Notas Raw (Directas)", justify="right", style="green")
        table.add_column("Notas Normalizadas (Escala 10)", justify="right", style="bold green")
        table.add_column("Interpretación", style="dim")
        
        table.add_row("Error Máximo", 
                      f"{metricas['raw']['max_error']:.2f}", 
                      f"{metricas['norm']['max_error']:.2f}",
                      "Menor es mejor (menor desvío extremo)")
        table.add_row("Error Medio (MAE)", 
                      f"{metricas['raw']['mae']:.2f}", 
                      f"{metricas['norm']['mae']:.2f}",
                      "Menor es mejor (desviación promedio)")
        table.add_row("Sesgo (Bias)", 
                      f"{metricas['raw']['bias']:.2f}", 
                      f"{metricas['norm']['bias']:.2f}",
                      ">0 sobrecalifica, <0 subcalifica")
        table.add_row("Coincidencia Exacta (Diff=0)", 
                      f"{metricas['raw']['exact_match']:.1f}%", 
                      f"{metricas['norm']['exact_match']:.1f}%",
                      "Mayor es mejor (precisión perfecta)")
        table.add_row("Coincidencia ±1 Punto", 
                      f"{metricas['raw']['match_within_1']:.1f}%", 
                      f"{metricas['norm']['match_within_1']:.1f}%",
                      "Mayor es mejor (margen de tolerancia)")
        
        console.print(table)
        
        # Tabla de matriz de confusión
        cm_table = Table(show_header=True, header_style="bold yellow", title="Matriz de Confusión de Aprobación (Umbral >= 4.0)")
        cm_table.add_column("Métrica de Clasificación", style="cyan")
        cm_table.add_column("Notas Raw", justify="right", style="green")
        cm_table.add_column("Notas Normalizadas", justify="right", style="bold green")
        
        raw_cm = metricas['raw']['confusion_matrix']
        norm_cm = metricas['norm']['confusion_matrix']
        
        cm_table.add_row("Verdaderos Positivos (TP)", f"{raw_cm['tp']} ({raw_cm['tp_pct']:.1f}%)", f"{norm_cm['tp']} ({norm_cm['tp_pct']:.1f}%)")
        cm_table.add_row("Falsos Negativos (FN)", f"{raw_cm['fn']} ({raw_cm['fn_pct']:.1f}%)", f"{norm_cm['fn']} ({norm_cm['fn_pct']:.1f}%)")
        cm_table.add_row("Falsos Positivos (FP)", f"{raw_cm['fp']} ({raw_cm['fp_pct']:.1f}%)", f"{norm_cm['fp']} ({norm_cm['fp_pct']:.1f}%)")
        cm_table.add_row("Verdaderos Negativos (TN)", f"{raw_cm['tn']} ({raw_cm['tn_pct']:.1f}%)", f"{norm_cm['tn']} ({norm_cm['tn_pct']:.1f}%)")
        cm_table.add_row("Exactitud (Accuracy)", f"{raw_cm['accuracy']:.1f}%", f"{norm_cm['accuracy']:.1f}%")
        cm_table.add_row("Sensibilidad (Recall)", f"{raw_cm['recall']:.1f}%", f"{norm_cm['recall']:.1f}%")
        cm_table.add_row("F1-Score", f"{raw_cm['f1']:.1f}%", f"{norm_cm['f1']:.1f}%")
        
        console.print(cm_table)
        
        # Mostrar histograma normalizado
        console.print("\n[bold]Distribución de diferencias (Esperado - Modelo Normalizado):[/bold]")
        for diff, pct in metricas['norm']['distribution'].items():
            count = metricas['norm']['distribution_counts'][diff]
            barras = "█" * int(round(pct / 2.5))
            signo = "+" if diff > 0 else ""
            console.print(f"  [bold]{signo}{diff:2d} pts[/bold]: {count:3d} casos ({pct:5.1f}%) {barras}")
            
        console.print()
    else:
        # Fallback sin Rich
        print("\n" + "="*60)
        print(f"MÉTRICAS DEL EXPERIMENTO: {nombre_archivo}")
        print(f"Casos Válidos: {n_validos}/{total_filas} ({n_validos/total_filas*100:.1f}%)")
        print(f"No parseados: {total_fallidas} ({total_fallidas/total_filas*100:.1f}%)")
        print("="*60)
        
        print(f"{'Métrica':<30} | {'Raw':<10} | {'Normalizado':<12}")
        print("-"*60)
        print(f"{'Error Máximo':<30} | {metricas['raw']['max_error']:<10.2f} | {metricas['norm']['max_error']:<12.2f}")
        print(f"{'Error Medio (MAE)':<30} | {metricas['raw']['mae']:<10.2f} | {metricas['norm']['mae']:<12.2f}")
        print(f"{'Sesgo (Bias)':<30} | {metricas['raw']['bias']:<10.2f} | {metricas['norm']['bias']:<12.2f}")
        print(f"{'Coincidencia Exacta':<30} | {metricas['raw']['exact_match']:<9.1f}% | {metricas['norm']['exact_match']:<11.1f}%")
        print(f"{'Coincidencia ±1 Punto':<30} | {metricas['raw']['match_within_1']:<9.1f}% | {metricas['norm']['match_within_1']:<11.1f}%")
        print("="*60)
        
        print("\nMATRIZ DE CONFUSIÓN DE APROBACIÓN (Umbral >= 4.0):")
        print("-" * 60)
        print(f"{'Métrica':<30} | {'Raw':<10} | {'Normalizado':<12}")
        print("-" * 60)
        raw_cm = metricas['raw']['confusion_matrix']
        norm_cm = metricas['norm']['confusion_matrix']
        print(f"{'Verdaderos Positivos (TP)':<30} | {raw_cm['tp']:<3} ({raw_cm['tp_pct']:4.1f}%) | {norm_cm['tp']:<3} ({norm_cm['tp_pct']:4.1f}%)")
        print(f"{'Falsos Negativos (FN)':<30} | {raw_cm['fn']:<3} ({raw_cm['fn_pct']:4.1f}%) | {norm_cm['fn']:<3} ({norm_cm['fn_pct']:4.1f}%)")
        print(f"{'Falsos Positivos (FP)':<30} | {raw_cm['fp']:<3} ({raw_cm['fp_pct']:4.1f}%) | {norm_cm['fp']:<3} ({norm_cm['fp_pct']:4.1f}%)")
        print(f"{'Verdaderos Negativos (TN)':<30} | {raw_cm['tn']:<3} ({raw_cm['tn_pct']:4.1f}%) | {norm_cm['tn']:<3} ({norm_cm['tn_pct']:4.1f}%)")
        print(f"{'Exactitud (Accuracy)':<30} | {raw_cm['accuracy']:<9.1f}% | {norm_cm['accuracy']:<11.1f}%")
        print(f"{'Sensibilidad (Recall)':<30} | {raw_cm['recall']:<9.1f}% | {norm_cm['recall']:<11.1f}%")
        print(f"{'F1-Score':<30} | {raw_cm['f1']:<9.1f}% | {norm_cm['f1']:<11.1f}%")
        print("="*60)
        
        print("\nDistribución de diferencias (Esperado - Modelo Normalizado):")
        for diff, pct in metricas['norm']['distribution'].items():
            count = metricas['norm']['distribution_counts'][diff]
            signo = "+" if diff > 0 else ""
            barras = "#" * int(round(pct / 3))
            print(f"  {signo}{diff:2d} pts: {count:3d} casos ({pct:5.1f}%) {barras}")
        print("="*60 + "\n")

def main():
    # Permitir pasar el archivo por línea de comandos
    if len(sys.argv) > 1:
        ruta_csv = sys.argv[1]
    else:
        # Selección interactiva
        ruta_csv = seleccionar_archivo_interactivo()
        
    if ruta_csv:
        procesar_csv(ruta_csv)
    else:
        print_info("Operación cancelada.")

if __name__ == "__main__":
    main()
