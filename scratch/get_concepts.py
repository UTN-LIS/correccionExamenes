import json

with open("documentacion/web_app_db.json", "r") as f:
    db = json.load(f)

for q_id in ["Q004474161", "Q799823558", "Q675600740", "Q205293180"]:
    if q_id in db["preguntas"]:
        print("="*80)
        print(f"QUESTION ID: {q_id}")
        print(f"Question: {db['preguntas'][q_id]['question_text']}")
        print(f"Ideal Answer: {db['preguntas'][q_id]['ideal_answer']}")
        print("Concepts:")
        for c in db["preguntas"][q_id]["conceptos"]:
            print(f"  - {c['tag']}: {c['descripcion']}")
