from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.models import User
from app.schemas.schemas import AuthRequest, AuthResponse
from app.utils.telegram_auth import verify_init_data, InvalidInitData
from app.utils.session import create_session_token

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/telegram", response_model=AuthResponse)
def login_with_telegram(payload: AuthRequest, db: Session = Depends(get_db)):
    try:
        tg_user = verify_init_data(payload.init_data)
    except InvalidInitData as e:
        raise HTTPException(status_code=401, detail=str(e))

    telegram_id = tg_user["id"]

    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        user = User(
            telegram_id=telegram_id,
            first_name=tg_user.get("first_name", ""),
            username=tg_user.get("username"),
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_session_token(user_id=user.id, telegram_id=user.telegram_id)

    return AuthResponse(
        token=token,
        user_id=user.id,
        first_name=user.first_name,
        is_premium=user.is_premium,
    )
