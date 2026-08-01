import csv
import numpy as np

csv_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/resultados_comparacion_independiente_15_20_65.csv"

true_grades = []
rango_labels = []

# Map label in row to its index
label_map = {
    "<INSUFICIENTE>": 0,
    "<ACEPTABLE>": 1,
    "<BUENO>": 2,
    "<EXCELENTE>": 3
}

with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        if not row:
            continue
        try:
            true_grades.append(float(row[2]))
            label = row[5].strip().upper()
            if label not in label_map:
                # Clean up brackets if any
                clean_label = f"<{label.replace('<','').replace('>','')}>\n"
                # Fallback to the one that matches
                found = False
                for k in label_map.keys():
                    if k.strip("<>") in label:
                        label = k
                        found = True
                        break
                if not found:
                    label = "<INSUFICIENTE>"
            rango_labels.append(label_map[label])
        except (ValueError, IndexError):
            continue

y_true = np.array(true_grades)
y_labels = np.array(rango_labels)

# We want to find values for indices 0, 1, 2, 3 in range [1, 10]
# to minimize MAE of: round(value_for_label) vs y_true
best_mae = float('inf')
best_vals = None

# Grid search for the 4 values
# index 0: 1.0 to 3.0 (step 0.5)
# index 1: 4.0 to 6.0 (step 0.5)
# index 2: 7.0 to 8.5 (step 0.5)
# index 3: 9.0 to 10.0 (step 0.5)
for v0 in np.arange(1.0, 3.5, 0.5):
    for v1 in np.arange(4.0, 6.5, 0.5):
        for v2 in np.arange(7.0, 9.0, 0.5):
            for v3 in np.arange(9.0, 10.5, 0.5):
                mapping = np.array([v0, v1, v2, v3])
                predictions = mapping[y_labels]
                rounded_preds = np.clip(np.round(predictions), 1, 10).astype(int)
                mae = np.mean(np.abs(rounded_preds - y_true))
                bias = np.mean(rounded_preds - y_true)
                
                if mae < best_mae:
                    best_mae = mae
                    best_vals = (v0, v1, v2, v3, bias)

print("--- OPTIMIZACIÓN DE VALORES DE MAPEO PARA RANGOS ---")
print(f"Valores originales: INSUFICIENTE=2.0, ACEPTABLE=5.0, BUENO=7.5, EXCELENTE=9.5")
v0, v1, v2, v3, bias = best_vals
print(f"Valores óptimos encontrados:")
print(f"  - <INSUFICIENTE>: {v0:.1f}")
print(f"  - <ACEPTABLE>:    {v1:.1f}")
print(f"  - <BUENO>:        {v2:.1f}")
print(f"  - <EXCELENTE>:    {v3:.1f}")
print(f"  - MAE Resultante:  {best_mae:.4f}")
print(f"  - Bias Resultante: {bias:.4f}")
