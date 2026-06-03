import pandas as pd

columnas = [
    "entry_id",
    "question_id",
    "question_text",
    "student_answer",
    "ideal_answer",
    "student_answer_length",
    "teacher_grade",
    "teacher_feedback"
]
# IDs que quieres conservar
ids_filtrar = [
    "Q004474161",
    "Q026190153",
    "Q058105629",
    "Q096739388",
    "Q127091047",
    "Q205293180",
    "Q320537127",
    "Q409295037",
    "Q434022307",
    "Q520973869",
    "Q589024667",
    "Q613282641",
    "Q675600740",
    "Q698312310",
    "Q735188186",
    "Q799823558",
    "Q856092512",
    "Q896336834",
    "Q901633271",
    "Q963462196",
    "Q977667967"
]

ids_filtrar1 = ["Q434022307"]

# Leer CSV original
df = pd.read_csv("dataset_es.csv")

# Filtrar filas
df_filtrado = df[df["question_id"].isin(ids_filtrar1)]
df_filtrado = df_filtrado[columnas]
# Guardar nuevo CSV
df_filtrado.to_csv("dataset_filtrado.csv", index=False, encoding="utf-8")

print(f"Filas encontradas: {len(df_filtrado)}")
