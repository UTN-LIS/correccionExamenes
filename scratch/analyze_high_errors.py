import pandas as pd

df = pd.read_csv("documentacion/resultados_comparacion_2026-08-13.csv")
df["abs_diff"] = df["Diferencia"].abs()
high_errors = df[df["abs_diff"] >= 3.0]

print(f"Total cases with error >= 3: {len(high_errors)}")
for idx, row in high_errors.iterrows():
    print("="*80)
    print(f"Line {idx+2} in CSV | Question ID: {row['Pregunta ID']}")
    print(f"Teacher Grade: {row['Nota Profesor']} | Agent Grade (Ensemble): {row['Nota Agente (Ensamble)']} | Diff: {row['Diferencia']}")
    print(f"Nota Conceptos: {row['Nota Conceptos (Exp 1)']} | Nota Directa: {row['Nota Directa (Exp 3)']}")
    print(f"Student Answer:\n{row['Respuesta estudiante']}")
