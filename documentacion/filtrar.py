import pandas as pd

columnas = [
    "question_id",
]

# Leer CSV original
df = pd.read_csv("dataset_filtrado.csv")

# Filtrar filas

df_filtrado = df[columnas]
# Guardar nuevo CSV
df_filtrado.to_csv("tiempos.csv", index=False, encoding="utf-8")

print(f"Filas encontradas: {len(df_filtrado)}")
