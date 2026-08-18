"""
Paste raw legal text below, and Gemini will generate multiple-choice questions
from it, then add them straight into the database using your existing schema.

Edit SUBJECT_TITLE, MODULE_LABEL, NUM_QUESTIONS, and LAW_TEXT below, then run:

    python generate_quiz.py

Safe to re-run: it reuses the same subject/module if the label already exists,
and skips a question if identical text is already in that module (so you can
run this many times with different chunks of law text to build up content).
"""
import json

from google import genai

from app.database import SessionLocal, Base, engine
from app.models.models import Subject, Module, Question
from app.config import settings

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- EDIT THIS SECTION ---
SUBJECT_TITLE = "Konstitutsiyaviy huquq"
MODULE_LABEL = "1-10"
NUM_QUESTIONS = 10  # how many questions to generate from this chunk of text

LAW_TEXT = """
Paste the actual law text here — one or several moddas (articles).
The more focused the text (e.g. one chapter at a time), the better the
questions will be. Very long pastes work too, just may take longer.
"""
# --- END EDIT SECTION ---


def generate_questions(law_text: str, count: int):
    client = genai.Client(api_key=settings.gemini_api_key)
    prompt = f"""Siz yuridik test tuzuvchi ekspertsiz. Quyidagi qonun matni asosida {count} ta test savoli tuzing.

Qoidalar:
- Savollar o'zbek tilida, aniq va milliy sertifikat imtihoni uslubida bo'lsin.
- Har bir savolda 4 ta javob varianti (A, B, C, D) bo'lsin, faqat bittasi to'g'ri.
- Noto'g'ri variantlar ishonarli chalg'ituvchi bo'lsin, lekin aniq noto'g'ri bo'lsin.
- Savollar faqat quyida berilgan matn asosida bo'lsin, matnda yo'q ma'lumot qo'shmang.
- Faqat quyidagi JSON massiv formatida javob bering — boshqa hech qanday matn, izoh yoki markdown yozmang:

[
  {{"text": "...", "option_a": "...", "option_b": "...", "option_c": "...", "option_d": "...", "correct_option": "a"}}
]

Qonun matni:
{law_text}
"""
    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt,
    )
    raw = response.text.strip()
    # Gemini sometimes wraps JSON in markdown code fences — strip them if present
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# --- Get or create subject/module (same pattern as seed.py) ---
subject = db.query(Subject).filter(Subject.title == SUBJECT_TITLE).first()
if not subject:
    subject = Subject(title=SUBJECT_TITLE, order=0)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    print(f"Created subject: {subject.title}")
else:
    print(f"Using existing subject: {subject.title}")

module = db.query(Module).filter(
    Module.subject_id == subject.id,
    Module.label == MODULE_LABEL,
).first()
if not module:
    module = Module(subject_id=subject.id, label=MODULE_LABEL, order=0)
    db.add(module)
    db.commit()
    db.refresh(module)
    print(f"Created module: {module.label}")
else:
    print(f"Using existing module: {module.label}")

# --- Generate and insert ---
print(f"\nAsking Gemini to generate {NUM_QUESTIONS} questions... (may take a moment)")
questions = generate_questions(LAW_TEXT, NUM_QUESTIONS)
print(f"Gemini returned {len(questions)} questions.\n")

added = 0
skipped = 0
for q in questions:
    exists = db.query(Question).filter(
        Question.module_id == module.id,
        Question.text == q["text"],
    ).first()
    if exists:
        skipped += 1
        continue
    question = Question(
        module_id=module.id,
        text=q["text"],
        option_a=q["option_a"],
        option_b=q["option_b"],
        option_c=q["option_c"],
        option_d=q["option_d"],
        correct_option=q["correct_option"].strip().lower(),
    )
    db.add(question)
    added += 1

db.commit()
print(f"Done. Added {added} new questions, skipped {skipped} duplicates.")
print(f"Module '{module.label}' now has {len(module.questions)} questions total.")
