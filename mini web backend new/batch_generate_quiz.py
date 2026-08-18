"""
Batch quiz generator — for laws with lots of moddalar (up to hundreds).

Instead of manually editing LAW_TEXT and re-running generate_quiz.py for every
chunk, this script:
  1. Reads a full law text from a .txt file
  2. Auto-splits it into individual moddalar using the "N-modda." pattern
  3. Groups moddalar into chunks (default: 8 per module)
  4. For each chunk, creates/reuses a module labeled by its article range
     (e.g. "11-18"), asks Gemini to generate questions, and inserts them
  5. Skips any chunk that already has questions in that module (safe to
     re-run / resume if it stops partway through)

Usage:
  1. Save the full law text as a .txt file (UTF-8), e.g. fuqarolik_kodeksi.txt
     Get this from lex.uz — copy the whole body of moddalar into the file.
  2. Edit the "EDIT THIS SECTION" block below.
  3. Run:
        python batch_generate_quiz.py
  4. If it stops partway (rate limit, network error, etc.) just run it again —
     already-filled modules are skipped automatically.
"""
import json
import re
import sys
import time

from google import genai

from app.database import SessionLocal, Base, engine
from app.models.models import Subject, Module, Question
from app.config import settings

Base.metadata.create_all(bind=engine)
db = SessionLocal()

# --- EDIT THIS SECTION ---
SUBJECT_TITLE = "Fuqarolik huquqi"          # must match (or will create) the subject
TXT_FILE_PATH = "fuqarolik_kodeksi.txt"     # path to the full law text file
MODDALAR_PER_MODULE = 8                     # how many articles grouped per module
QUESTIONS_PER_MODDA = 1                     # questions generated per modda (1-2 recommended)
DELAY_BETWEEN_CALLS = 3                     # seconds to wait between Gemini calls (avoid rate limits)
# --- END EDIT SECTION ---


def split_into_moddalar(full_text: str):
    """Splits raw law text into a list of (article_number, article_text) using the
    '<N>-modda.' marker pattern common in Uzbek legal texts."""
    pattern = re.compile(r"(\d+)-modda\.")
    matches = list(pattern.finditer(full_text))
    if not matches:
        print("ERROR: No '<N>-modda.' markers found in the text file. "
              "Check that the text uses that exact format, or adjust the regex.")
        sys.exit(1)

    moddalar = []
    for i, m in enumerate(matches):
        number = int(m.group(1))
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(full_text)
        moddalar.append((number, full_text[start:end].strip()))
    return moddalar


def chunk_moddalar(moddalar, size):
    for i in range(0, len(moddalar), size):
        yield moddalar[i:i + size]


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
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())


# --- Load and split the law text ---
try:
    with open(TXT_FILE_PATH, "r", encoding="utf-8") as f:
        full_text = f.read()
except FileNotFoundError:
    print(f"ERROR: Could not find '{TXT_FILE_PATH}'. Make sure the file exists "
          f"in this folder (or update TXT_FILE_PATH to the correct path).")
    sys.exit(1)

moddalar = split_into_moddalar(full_text)
print(f"Found {len(moddalar)} moddalar in '{TXT_FILE_PATH}' "
      f"(modda {moddalar[0][0]} to modda {moddalar[-1][0]}).")

chunks = list(chunk_moddalar(moddalar, MODDALAR_PER_MODULE))
print(f"Split into {len(chunks)} modules of ~{MODDALAR_PER_MODULE} moddalar each.\n")

# --- Get or create subject ---
subject = db.query(Subject).filter(Subject.title == SUBJECT_TITLE).first()
if not subject:
    subject = Subject(title=SUBJECT_TITLE, order=0)
    db.add(subject)
    db.commit()
    db.refresh(subject)
    print(f"Created subject: {subject.title}")
else:
    print(f"Using existing subject: {subject.title}")

total_added = 0
total_skipped_modules = 0

for chunk in chunks:
    first_num = chunk[0][0]
    last_num = chunk[-1][0]
    label = f"{first_num}-{last_num}"
    chunk_text = "\n\n".join(text for _, text in chunk)

    module = db.query(Module).filter(
        Module.subject_id == subject.id,
        Module.label == label,
    ).first()
    if not module:
        module = Module(subject_id=subject.id, label=label, order=first_num)
        db.add(module)
        db.commit()
        db.refresh(module)

    existing_count = db.query(Question).filter(Question.module_id == module.id).count()
    if existing_count > 0:
        print(f"Module '{label}': already has {existing_count} questions, skipping.")
        total_skipped_modules += 1
        continue

    target_count = len(chunk) * QUESTIONS_PER_MODDA
    print(f"Module '{label}': generating {target_count} questions "
          f"from {len(chunk)} moddalar...")

    try:
        questions = generate_questions(chunk_text, target_count)
    except Exception as e:
        print(f"  FAILED on module '{label}': {e}")
        print(f"  Skipping this module — re-run the script later to retry it "
              f"(already-filled modules will be skipped, this one won't be).")
        continue

    added = 0
    for q in questions:
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
    total_added += added
    print(f"  Added {added} questions to module '{label}'.")

    time.sleep(DELAY_BETWEEN_CALLS)

print(f"\nDone. Added {total_added} questions total across {len(chunks)} modules "
      f"({total_skipped_modules} modules already had content and were skipped).")
