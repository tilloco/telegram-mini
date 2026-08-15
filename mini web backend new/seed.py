"""
Quick way to add real content to the database without building an admin panel.
Edit the data below with your actual subjects/modules/questions, then run:

    python seed.py

Safe to run multiple times — it won't duplicate a subject if the title already exists.
"""
from app.database import SessionLocal, Base, engine
from app.models.models import Subject, Module, Question

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- EDIT THIS SECTION with your real content ---
DATA = [
    {
        "subject": "Konstitutsiyaviy huquq",
        "modules": [
            {
                "label": "1-10",
                "questions": [
                    {
                        "text": "O'zbekiston Respublikasi Konstitutsiyasi qachon qabul qilingan?",
                        "options": {"a": "1991-yil", "b": "1992-yil", "c": "1993-yil", "d": "1994-yil"},
                        "correct": "b",
                    },
                    {
                        "text": "O'zbekiston Respublikasining davlat tili qanday belgilangan?",
                        "options": {"a": "Rus tili", "b": "O'zbek tili", "c": "Ikkala til", "d": "Belgilanmagan"},
                        "correct": "b",
                    },
                ],
            }
        ],
    }
]
# --- END EDIT SECTION ---

for subj_data in DATA:
    subject = db.query(Subject).filter(Subject.title == subj_data["subject"]).first()
    if not subject:
        subject = Subject(title=subj_data["subject"], order=0)
        db.add(subject)
        db.commit()
        db.refresh(subject)
        print(f"Created subject: {subject.title}")
    else:
        print(f"Subject already exists: {subject.title}")

    for mod_data in subj_data["modules"]:
        module = db.query(Module).filter(
            Module.subject_id == subject.id,
            Module.label == mod_data["label"],
        ).first()
        if not module:
            module = Module(subject_id=subject.id, label=mod_data["label"], order=0)
            db.add(module)
            db.commit()
            db.refresh(module)
            print(f"  Created module: {module.label}")

            for q in mod_data["questions"]:
                question = Question(
                    module_id=module.id,
                    text=q["text"],
                    option_a=q["options"]["a"],
                    option_b=q["options"]["b"],
                    option_c=q["options"]["c"],
                    option_d=q["options"]["d"],
                    correct_option=q["correct"],
                )
                db.add(question)
            db.commit()
            print(f"    Added {len(mod_data['questions'])} questions")
        else:
            print(f"  Module already exists: {module.label}")

print("\nDone.")
