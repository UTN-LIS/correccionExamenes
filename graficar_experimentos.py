#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Script de Visualización de Rendimiento de Experimentos de Calificación con IA
Autor: Antigravity
Propósito: Cargar los resultados del CSV de experimentos paralelos y generar
           gráficos de alta calidad para analizar el comportamiento y precisión
           de cada experimento frente a las notas de referencia (esperadas).
"""

import os
import sys
import math
import csv
import matplotlib.pyplot as plt
import numpy as np

# Configuración estética de Matplotlib para un diseño premium y moderno
plt.rcParams['figure.facecolor'] = '#F8FAFC'  # Fondo de la figura (slate 50)
plt.rcParams['axes.facecolor'] = '#FFFFFF'    # Fondo de los gráficos (blanco)
plt.rcParams['axes.edgecolor'] = '#E2E8F0'    # Bordes de los gráficos (slate 200)
plt.rcParams['axes.grid'] = True
plt.rcParams['grid.color'] = '#F1F5F9'        # Líneas de cuadrícula muy suaves (slate 100)
plt.rcParams['grid.linewidth'] = 1.0
plt.rcParams['font.family'] = 'sans-serif'
plt.rcParams['font.sans-serif'] = ['DejaVu Sans', 'Arial', 'Liberation Sans']
plt.rcParams['text.color'] = '#1E293B'        # Color de texto principal (slate 800)
plt.rcParams['axes.labelcolor'] = '#475569'   # Color de etiquetas de ejes (slate 600)
plt.rcParams['xtick.color'] = '#64748B'       # Color de ticks X (slate 500)
plt.rcParams['ytick.color'] = '#64748B'       # Color de ticks Y (slate 500)

def clean_float(val):
    """
    Limpia y convierte a flotante un valor que puede tener formato de coma decimal o estar vacío.
    """
    if val is None:
        return None
    if isinstance(val, (int, float)):
        return float(val)
    
    val_str = str(val).strip()
    if not val_str or val_str.lower() in ('nan', 'null', ''):
        return None
    
    # Reemplazar coma decimal por punto
    val_str = val_str.replace(',', '.')
    try:
        return float(val_str)
    except ValueError:
        return None

def map_category_to_bounds(cat_str):
    """
    Mapea las categorías del experimento-categoria a sus cotas inferior y superior.
    Cada categoría tiene 2.5 puntos de rango en una escala de 0 a 10.
    """
    if not isinstance(cat_str, str):
        return None, None
    
    cat = cat_str.strip().upper()
    
    # Mapeo según especificación:
    # <SIN_RESPUESTA>: [0.0, 2.5]
    # <INSUFICIENTE> / <INSUFFICIENTE> (con typo): (2.5, 5.0]
    # <ACEPTABLE>: (5.0, 7.5]
    # <EXCELENTE>: (7.5, 10.0]
    if cat == '<SIN_RESPUESTA>':
        return 0.0, 2.5
    elif cat in ('<INSUFICIENTE>', '<INSUFFICIENTE>'):
        return 2.5, 5.0
    elif cat == '<ACEPTABLE>':
        return 5.0, 7.5
    elif cat == '<EXCELENTE>':
        return 7.5, 10.0
    else:
        # Retornar None para categorías desconocidas o no parseables
        return None, None

def cargar_datos(ruta_csv):
    """
    Carga el archivo CSV y procesa las columnas necesarias.
    """
    if not os.path.exists(ruta_csv):
        print(f"ERROR: El archivo '{ruta_csv}' no existe.")
        sys.exit(1)
        
    datos = []
    
    # Intentar leer con encoding común
    with open(ruta_csv, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for idx, row in enumerate(reader):
            # Parsear esperado (esencial como referencia)
            esp = clean_float(row.get('esperado'))
            if esp is None:
                continue  # Omitir filas sin valor esperado
            
            # Parsear Experimento-nota
            exp_nota = clean_float(row.get('Experimento-nota'))
            
            # Parsear nota-por-varios-conceptos
            nota_conceptos = clean_float(row.get('nota-por-varios-conceptos'))
            
            # Parsear experimento-categoria y sus cotas
            cat_str = row.get('experimento-categoria', '')
            cota_inf, cota_sup = map_category_to_bounds(cat_str)
            
            datos.append({
                'index': idx,
                'question_id': row.get('question_id', f'Q_{idx}'),
                'esperado': esp,
                'experimento_nota': exp_nota,
                'nota_conceptos': nota_conceptos,
                'categoria': cat_str,
                'cota_inf': cota_inf,
                'cota_sup': cota_sup
            })
            
    return datos

def generar_graficos(datos, ruta_salida):
    """
    Genera el tablero de visualización comparativo.
    """
    # 1. Preparar datos para las gráficas
    # Filtrar datos válidos para experimentos numéricos
    datos_num = [d for d in datos if d['experimento_nota'] is not None]
    datos_conceptos = [d for d in datos if d['nota_conceptos'] is not None]
    datos_cat = [d for d in datos if d['cota_inf'] is not None]
    
    # Agrupar valores numéricos por nota de referencia (esperado) para obtener las curvas promedio (rectas de tendencia)
    # Experimento-nota
    esp_valores_nota = {}
    for d in datos_num:
        esp_valores_nota.setdefault(d['esperado'], []).append(d['experimento_nota'])
    
    esp_unicos_nota = sorted(esp_valores_nota.keys())
    promedios_nota = [np.mean(esp_valores_nota[e]) for e in esp_unicos_nota]
    
    # nota-por-varios-conceptos
    esp_valores_conceptos = {}
    for d in datos_conceptos:
        esp_valores_conceptos.setdefault(d['esperado'], []).append(d['nota_conceptos'])
        
    esp_unicos_conceptos = sorted(esp_valores_conceptos.keys())
    promedios_conceptos = [np.mean(esp_valores_conceptos[e]) for e in esp_unicos_conceptos]

    # experimento-categoria (promedio de cotas por nota esperada)
    esp_valores_cat = {}
    for d in datos_cat:
        esp_valores_cat.setdefault(d['esperado'], []).append((d['cota_inf'], d['cota_sup']))
        
    esp_unicos_cat = sorted(esp_valores_cat.keys())
    promedios_cota_inf = [np.mean([x[0] for x in esp_valores_cat[e]]) for e in esp_unicos_cat]
    promedios_cota_sup = [np.mean([x[1] for x in esp_valores_cat[e]]) for e in esp_unicos_cat]

    # Crear la figura del panel con 2 subplots principales
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7.5))
    fig.suptitle('Análisis de Experimentos de Corrección con IA frente al Profesor', 
                 fontsize=18, fontweight='bold', color='#0F172A', y=0.96)
    
    # -------------------------------------------------------------
    # SUBPLOT 1: Comparación de Notas Numéricas (Rectas y Dispersión)
    # -------------------------------------------------------------
    # Línea de referencia (Profesor)
    lims = [0, 10]
    ax1.plot(lims, lims, color='#475569', linestyle='--', linewidth=2, label='Esperado (Profesor)', zorder=2)
    
    # Puntos de dispersión individuales (con baja opacidad para evitar solapamiento)
    # Experimento-nota (puntos lilas/violetas)
    ax1.scatter([d['esperado'] for d in datos_num], [d['experimento_nota'] for d in datos_num],
                color='#818CF8', alpha=0.35, edgecolors='none', s=45, label='Casos: Experimento-nota', zorder=3)
    
    # nota-por-varios-conceptos (puntos celestes/teales)
    ax1.scatter([d['esperado'] for d in datos_conceptos], [d['nota_conceptos'] for d in datos_conceptos],
                color='#2DD4BF', alpha=0.3, edgecolors='none', s=35, label='Casos: Nota por varios conceptos', zorder=3)
    
    # Rectas promedio (Líneas de tendencia)
    ax1.plot(esp_unicos_nota, promedios_nota, color='#4F46E5', marker='o', linewidth=3, markersize=8,
             label='Tendencia: Experimento-nota', zorder=5)
    ax1.plot(esp_unicos_conceptos, promedios_conceptos, color='#0D9488', marker='s', linewidth=2.5, markersize=7,
             label='Tendencia: Nota por varios conceptos', zorder=4)
    
    ax1.set_title('Comparación de Calificaciones Numéricas', fontsize=14, fontweight='semibold', pad=15)
    ax1.set_xlabel('Nota Esperada (Profesor)', fontsize=12, labelpad=10)
    ax1.set_ylabel('Nota Asignada por IA', fontsize=12, labelpad=10)
    ax1.set_xlim(-0.5, 10.5)
    ax1.set_ylim(-0.5, 10.5)
    ax1.set_xticks(range(11))
    ax1.set_yticks(range(11))
    ax1.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', framealpha=0.9)
    
    # -------------------------------------------------------------
    # SUBPLOT 2: Experimento de Categorías (Cotas Superior e Inferior)
    # -------------------------------------------------------------
    # Línea de referencia (Profesor)
    ax2.plot(lims, lims, color='#475569', linestyle='--', linewidth=2, label='Esperado (Profesor)', zorder=2)
    
    # Región sombreada del intervalo promedio predicho por la categoría para cada nota esperada
    ax2.fill_between(esp_unicos_cat, promedios_cota_inf, promedios_cota_sup, 
                     color='#F87171', alpha=0.2, label='Banda de Categoría Promedio (Cota Inf-Sup)', zorder=1)
    
    # Graficar las cotas promedio como líneas límite
    ax2.plot(esp_unicos_cat, promedios_cota_inf, color='#EF4444', linestyle=':', linewidth=1.8, label='Límite Inferior Promedio', zorder=4)
    ax2.plot(esp_unicos_cat, promedios_cota_sup, color='#EF4444', linestyle=':', linewidth=1.8, label='Límite Superior Promedio', zorder=4)
    
    # Puntos individuales clasificados según acierto de cota
    correctos_x, correctos_y = [], []
    sobre_x, sobre_y = [], []   # IA sobreestimó (el valor esperado es menor que la cota inferior)
    sub_x, sub_y = [], []       # IA subestimó (el valor esperado es mayor que la cota superior)
    
    for d in datos_cat:
        esp = d['esperado']
        cota_i = d['cota_inf']
        cota_s = d['cota_sup']
        
        # Evaluar si la nota real del profesor cae en el intervalo de la categoría predicha por la IA
        if cota_i <= esp <= cota_s:
            correctos_x.append(esp)
            correctos_y.append((cota_i + cota_s) / 2) # Graficar en el centro del intervalo
        elif esp < cota_i:
            sobre_x.append(esp)
            sobre_y.append((cota_i + cota_s) / 2)
        else:
            sub_x.append(esp)
            sub_y.append((cota_i + cota_s) / 2)
            
    # Graficar los puntos individuales por tipo de acierto
    ax2.scatter(correctos_x, correctos_y, color='#10B981', alpha=0.6, edgecolors='none', s=50, 
                label='Categoría Correcta (Nota real dentro del intervalo)', zorder=3)
    ax2.scatter(sobre_x, sobre_y, color='#EF4444', alpha=0.6, edgecolors='none', s=50, 
                label='IA Sobrecalificó (Nota real menor que la categoría)', zorder=3)
    ax2.scatter(sub_x, sub_y, color='#3B82F6', alpha=0.6, edgecolors='none', s=50, 
                label='IA Subcalificó (Nota real mayor que la categoría)', zorder=3)
    
    ax2.set_title('Evaluación de Intervalos (experimento-categoria)', fontsize=14, fontweight='semibold', pad=15)
    ax2.set_xlabel('Nota Esperada (Profesor)', fontsize=12, labelpad=10)
    ax2.set_ylabel('Centro de la Categoría Predicha', fontsize=12, labelpad=10)
    ax2.set_xlim(-0.5, 10.5)
    ax2.set_ylim(-0.5, 10.5)
    ax2.set_xticks(range(11))
    ax2.set_yticks(range(11))
    ax2.legend(loc='upper left', frameon=True, facecolor='#FFFFFF', edgecolor='#E2E8F0', framealpha=0.9)
    
    # Ajustar espaciado
    plt.tight_layout(rect=[0, 0, 1, 0.93])
    
    # Guardar la gráfica en disco
    plt.savefig(ruta_salida, dpi=300, bbox_inches='tight')
    plt.close()
    print(f"ÉXITO: Gráficas de experimentos guardadas en '{ruta_salida}'")

def imprimir_estadisticas_categoria(datos):
    """
    Calcula y muestra estadísticas de precisión de la predicción de categorías.
    """
    total = 0
    correctos = 0
    subcalificados = 0
    sobrecalificados = 0
    
    for d in datos:
        if d['cota_inf'] is None:
            continue
        total += 1
        esp = d['esperado']
        cota_i = d['cota_inf']
        cota_s = d['cota_sup']
        
        if cota_i <= esp <= cota_s:
            correctos += 1
        elif esp < cota_i:
            sobrecalificados += 1
        else:
            subcalificados += 1
            
    if total == 0:
        print("No se encontraron datos válidos de categorías para calcular estadísticas.")
        return
        
    print("\n" + "="*50)
    print("ESTADÍSTICAS DEL EXPERIMENTO DE CATEGORÍAS")
    print(f"Total de casos evaluados: {total}")
    print("-"*50)
    print(f"Acierto de Rango (Nota real dentro de categoría): {correctos} casos ({correctos/total*100:.2f}%)")
    print(f"Subcalificados (Nota real por encima del rango):  {subcalificados} casos ({subcalificados/total*100:.2f}%)")
    print(f"Sobrecalificados (Nota real por debajo del rango): {sobrecalificados} casos ({sobrecalificados/total*100:.2f}%)")
    print("="*50)

def main():
    # Ruta por defecto
    ruta_csv = 'documentacion/Informe-3-experimentos-paralelos.csv'
    
    # Si se pasa un argumento por línea de comandos, usarlo
    if len(sys.argv) > 1:
        ruta_csv = sys.argv[1]
        
    ruta_salida = os.path.splitext(ruta_csv)[0] + '_grafico.png'
    
    print(f"Cargando datos desde: '{ruta_csv}'...")
    datos = cargar_datos(ruta_csv)
    
    print(f"Generando gráficos comparativos...")
    generar_graficos(datos, ruta_salida)
    
    # Imprimir estadísticas resumen para la consola
    imprimir_estadisticas_categoria(datos)

if __name__ == '__main__':
    main()
