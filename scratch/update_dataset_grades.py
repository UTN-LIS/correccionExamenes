import csv
import json
import os

csv_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/dataset_simulado_pruebas.csv"
db_path = "/home/franco-sosa/Documentos/correccionExamenes/documentacion/web_app_db.json"

def update_grade(grade_val):
    try:
        val = float(grade_val)
        if val == 0.0:
            return 1.0
        elif val == 1.0:
            return 2.0
        elif val == 2.0:
            return 3.0
    except ValueError:
        pass
    return grade_val

# 1. Update CSV
print("Actualizando CSV...")
rows = []
fieldnames = []
if os.path.exists(csv_path):
    with open(csv_path, "r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        for row in reader:
            row["teacher_grade"] = str(update_grade(row["teacher_grade"]))
            rows.append(row)
            
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print("CSV actualizado con éxito.")
else:
    print("No se encontró el CSV en la ruta especificada.")

# 2. Update JSON DB
print("Actualizando JSON DB...")
if os.path.exists(db_path):
    with open(db_path, "r", encoding="utf-8") as f:
        db = json.load(f)
        
    def recurse_update(data):
        if isinstance(data, dict):
            for k, v in data.items():
                if k == "teacher_grade":
                    data[k] = update_grade(v)
                else:
                    recurse_update(v)
        elif isinstance(data, list):
            for item in data:
                recurse_update(item)
                
    recurse_update(db)
    
    with open(db_path, "w", encoding="utf-8") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)
    print("JSON DB actualizado con éxito.")
else:
    print("No se encontró el JSON DB en la ruta especificada.")
