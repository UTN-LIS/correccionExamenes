import csv
import numpy as np

csv_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/resultados_comparacion_independiente_15_20_65.csv"

true_grades = []
exp1_grades = []
exp2_grades = []
exp3_grades = []

with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if not row:
            continue
        try:
            true_grades.append(float(row[2]))
            exp1_grades.append(float(row[6]))
            exp2_grades.append(float(row[7]))
            exp3_grades.append(float(row[8]))
        except ValueError:
            continue

y_true = np.array(true_grades)
y_exp1 = np.array(exp1_grades)
y_exp2 = np.array(exp2_grades)
y_exp3 = np.array(exp3_grades)

def get_metrics(predictions, true_vals):
    predictions = np.clip(np.round(predictions), 1, 10).astype(int)
    mae = np.mean(np.abs(predictions - true_vals))
    bias = np.mean(predictions - true_vals)
    exact_match = np.mean(predictions == true_vals) * 100
    tolerance_1 = np.mean(np.abs(predictions - true_vals) <= 1) * 100
    return mae, bias, exact_match, tolerance_1

manual_configs = [
    (0.15, 0.20, 0.65, "Configuración del Usuario"),
    (0.10, 0.05, 0.85, "Optimización Simplificada A"),
    (0.10, 0.00, 0.90, "Optimización Simplificada B"),
    (0.00, 0.00, 1.00, "Solo Experimento 3 (Nota Directa)"),
    (0.12, 0.02, 0.86, "Configuración Óptima Absoluta")
]

print("--- COMPARATIVA DE CONFIGURACIONES MANUALES ---")
for w1, w2, w3, desc in manual_configs:
    y_pred = w1 * y_exp1 + w2 * y_exp2 + w3 * y_exp3
    mae, bias, em, tol = get_metrics(y_pred, y_true)
    print(f"{desc} (w1={w1:.2f}, w2={w2:.2f}, w3={w3:.2f}):")
    print(f"  MAE: {mae:.4f}, Bias: {bias:.4f}, Exact Match: {em:.2f}%, Tol±1: {tol:.2f}%")
