import csv
import json
import os

csv_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/dataset_simulado_pruebas.csv"
db_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/web_app_db.json"

if not os.path.exists(csv_path):
    print("CSV no encontrado.")
    exit(1)

# Read CSV rows
csv_rows = []
with open(csv_path, "r", encoding="utf-8-sig") as f:
    reader = csv.DictReader(f)
    for row in reader:
        csv_rows.append(row)

# Load existing DB
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
else:
    db = {"preguntas": {}, "respuestas_cargadas": [], "resultados": {}, "proceso_correccion": {"status": "idle"}}

# Build respuestas_cargadas
respuestas_cargadas = []
for row in csv_rows:
    respuestas_cargadas.append({
        "question_id": row["question_id"].strip(),
        "alumno_id": str(row["entry_id"]).strip(),
        "student_answer": row["student_answer"].strip()
    })

# Build respuestas_comparar
respuestas_comparar = []
for row in csv_rows:
    respuestas_comparar.append({
        "question_id": row["question_id"].strip(),
        "student_answer": row["student_answer"].strip(),
        "teacher_grade": float(row["teacher_grade"])
    })

# Update DB
db["respuestas_cargadas"] = respuestas_cargadas
db["respuestas_comparar"] = respuestas_comparar

# Clear old results/metrics to allow a fresh run
db["resultados"] = {}
db["proceso_correccion"] = {
    "status": "idle",
    "total": len(respuestas_cargadas),
    "procesado": 0,
    "errores": 0
}
db["proceso_comparacion"] = {
    "status": "idle",
    "total": len(respuestas_comparar),
    "procesado": 0,
    "errores": 0,
    "mae": 0.0
}
db["resultados_comparacion"] = {}

with open(db_path, "w", encoding="utf-8") as f:
    json.dump(db, f, indent=2, ensure_ascii=False)

print(f"Base de datos web_app_db.json actualizada con {len(csv_rows)} registros de comparación y carga.")
