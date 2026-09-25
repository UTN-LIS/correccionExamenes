import json
import pandas as pd
from sklearn.metrics import confusion_matrix

# 1. Cargar dataset
df = pd.read_csv("Tercer-exp-entropia.csv")


# 2. Identificar y filtrar el bug del "10"
def es_bug_10(row):
    # El bug ocurre si la nota esperada era 10 y el "1" aparece como candidato con probabilidad > 0
    if row["esperado"] == 10:
        candidatos = row["top_3_notas_json"]
        if isinstance(candidatos, str):
            candidatos = json.loads(candidatos)
        return any(
            item.get("nota") == 1 and item.get("probabilidad", 0) > 0
            for item in candidatos
        )
    return False


df["es_bug"] = df.apply(es_bug_10, axis=1)
casos_bug = df["es_bug"].sum()

# Dataset filtrado sin contaminación
df_clean = df[~df["es_bug"]].copy()

# 3. Error medio (MAE) de nota_directa vs esperado
mae_directo = (df_clean["nota_directa"] - df_clean["esperado"]).abs().mean()


# 4. Error medio probabilístico para entropía != 1 (Valor Esperado = ∑ nota * prob)
def calcular_nota_ponderada(row):
    probs = row["top_3_notas_json"]
    if isinstance(probs, str):
        probs = json.loads(probs)
    return sum(
        float(item["nota"]) * float(item["probabilidad"]) for item in probs
    )


df_h_diff = df_clean[df_clean["entropia"] != 1.0].copy()
df_h_diff["nota_ponderada"] = df_h_diff.apply(calcular_nota_ponderada, axis=1)
mae_probabilistico = (
    df_h_diff["nota_ponderada"] - df_h_diff["esperado"]
).abs().mean()

# 5. Matrices de Confusión

# Caso A: Entropía == 1 (Éxito si nota_directa == esperado)
df_h1 = df_clean[df_clean["entropia"] == 1.0].copy()
labels_h1 = sorted(
    list(set(df_h1["esperado"]).union(set(df_h1["nota_directa"])))
)



# Caso B: Entropía != 1 (Éxito si el valor esperado está entre los candidatos con prob > 0)
def esta_en_top(row):
    candidatos = row["top_3_notas_json"]
    if isinstance(candidatos, str):
        candidatos = json.loads(candidatos)
    return any(
        item.get("nota") == row["esperado"] and item.get("probabilidad", 0) > 0
        for item in candidatos
    )


df_h_diff["exito"] = df_h_diff.apply(esta_en_top, axis=1)

# Matriz/Tabla de Contingencia: Nota Esperada vs Éxito (True/False)
matrix_h_diff = pd.crosstab(
    df_h_diff["esperado"],
    df_h_diff["exito"],
    rownames=["Nota Esperada"],
    colnames=["Éxito en Top"],
)

# 6. Salida de resultados
print(f"Casos con bug del '10' eliminados: {casos_bug}")
print(f"Error medio (nota directa): {mae_directo:.4f}")
print(f"Error medio probabilístico (H != 1): {mae_probabilistico:.4f}")

print(
    "\n--- Matriz de confusión (H != 1 - Éxito en Top Candidates) ---\n",
    matrix_h_diff,
)