import os
from datetime import date, timedelta

from fastapi import APIRouter, HTTPException, Query
from sqlalchemy import func
from sqlalchemy.orm import Session
from fastapi import Depends

from app.database import get_db
from app.models.models import User, Progress

router = APIRouter(prefix="/admin", tags=["admin"])

# Set this in Render -> your backend service -> Environment -> Add Environment Variable
# Key:   ADMIN_KEY
# Value: (o'zingiz o'ylab topgan uzun, tasodifiy parol, masalan bir necha so'z + raqam)
ADMIN_KEY = os.environ.get("ADMIN_KEY")


def check_key(key: str):
    if not ADMIN_KEY:
        raise HTTPException(status_code=500, detail="ADMIN_KEY sozlanmagan (Render Environment'da qo'shing)")
    if key != ADMIN_KEY:
        raise HTTPException(status_code=403, detail="Noto'g'ri kalit")


@router.get("/stats")
def get_stats(key: str = Query(...), db: Session = Depends(get_db)):
    check_key(key)

    total_users = db.query(func.count(User.id)).scalar()

    today = date.today()
    users_today = db.query(func.count(User.id)).filter(
        func.date(User.created_at) == today
    ).scalar()

    week_ago = today - timedelta(days=7)
    users_last_7_days = db.query(func.count(User.id)).filter(
        func.date(User.created_at) >= week_ago
    ).scalar()

    total_answers = db.query(func.coalesce(func.sum(Progress.last_question_index), 0)).scalar()
    total_correct = db.query(func.coalesce(func.sum(Progress.correct_count), 0)).scalar()

    # Users per day, last 14 days - useful for a simple growth chart
    daily_rows = (
        db.query(func.date(User.created_at).label("day"), func.count(User.id).label("count"))
        .filter(func.date(User.created_at) >= today - timedelta(days=14))
        .group_by(func.date(User.created_at))
        .order_by(func.date(User.created_at))
        .all()
    )
    daily_signups = [{"date": str(row.day), "new_users": row.count} for row in daily_rows]

    return {
        "total_users": total_users,
        "new_users_today": users_today,
        "new_users_last_7_days": users_last_7_days,
        "total_questions_answered": int(total_answers),
        "total_correct_answers": int(total_correct),
        "daily_signups_last_14_days": daily_signups,
    }
