from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import Question, Progress
from app.schemas.schemas import QuestionOut, AnswerRequest, AnswerResponse, ProgressOut
from app.dependencies import get_current_user

router = APIRouter(prefix="/quiz", tags=["quiz"])


@router.get("/modules/{module_id}/questions", response_model=list[QuestionOut])
def get_questions(module_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    return db.query(Question).filter(Question.module_id == module_id).all()


@router.post("/answer", response_model=AnswerResponse)
def submit_answer(payload: AnswerRequest, db: Session = Depends(get_db), user=Depends(get_current_user)):
    question = db.query(Question).filter(Question.id == payload.question_id).first()
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")

    # --- Grade the answer ---
    is_correct = payload.selected_option.lower() == question.correct_option.lower()

    # --- Update progress ---
    progress = db.query(Progress).filter(
        Progress.user_id == user.id,
        Progress.module_id == question.module_id,
    ).first()

    if not progress:
        progress = Progress(
            user_id=user.id,
            module_id=question.module_id,
            last_question_index=0,
            correct_count=0,
        )
        db.add(progress)

    progress.last_question_index = (progress.last_question_index or 0) + 1
    if is_correct:
        progress.correct_count = (progress.correct_count or 0) + 1

    db.commit()

    return AnswerResponse(
        correct=is_correct,
        correct_option=question.correct_option,
        free_questions_remaining=None,
    )


@router.get("/modules/{module_id}/progress", response_model=ProgressOut)
def get_progress(module_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    progress = db.query(Progress).filter(
        Progress.user_id == user.id,
        Progress.module_id == module_id,
    ).first()

    if not progress:
        return ProgressOut(module_id=module_id, last_question_index=0, correct_count=0, completed=False)

    return progress
