from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.utils.ai import ask_ai
from app.config import settings
import traceback

router = APIRouter(prefix="/ai", tags=["ai"])

class AskRequest(BaseModel):
    question: str
    context: str | None = None

@router.post("/ask")
async def ask(payload: AskRequest):
    if not settings.gemini_api_key:
        raise HTTPException(status_code=503, detail="AI assistant is not configured yet.")
    try:
        answer = await ask_ai(payload.question, payload.context or "")
        return {"answer": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}")