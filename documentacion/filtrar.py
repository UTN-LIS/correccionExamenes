import pandas as pd

columnas = [
    "tiempo",
]

# Leer CSV original
df = pd.read_csv("Qwen2-71PreguntaConEjemplos_2048tokens.csv")

# Filtrar filas

df_filtrado = df[columnas]
# Guardar nuevo CSV
df_filtrado.to_csv("tiempos.csv", index=False, encoding="utf-8")

print(f"Filas encontradas: {len(df_filtrado)}")
