import json

try:
    with open("documentacion/web_app_db.json", "r") as f:
        db = json.load(f)
except Exception as e:
    print(f"Error loading web_app_db.json: {e}")
    exit(1)

respuestas = db.get("respuestas_comparar", [])
print(f"Total respuestas to compare: {len(respuestas)}")

# Inspecting fields
malformed = 0
for idx, r in enumerate(respuestas):
    # Check keys
    required_keys = ["question_id", "student_answer", "teacher_grade"]
    missing = [k for k in required_keys if k not in r]
    if missing:
        print(f"Error at index {idx}: Missing keys {missing}. Entry: {r}")
        malformed += 1
        continue
    
    # Check teacher_grade type
    tg = r["teacher_grade"]
    try:
        float(tg)
    except (ValueError, TypeError) as e:
        print(f"Error at index {idx}: teacher_grade is not numeric: {tg} (Type: {type(tg)}). Entry: {r}")
        malformed += 1
        continue
        
    # Check student_answer
    sa = r["student_answer"]
    if not isinstance(sa, str):
        print(f"Error at index {idx}: student_answer is not a string. Entry: {r}")
        malformed += 1
        continue

print(f"Validation completed. Malformed entries: {malformed}")
