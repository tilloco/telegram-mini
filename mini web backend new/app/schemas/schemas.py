from datetime import datetime
from pydantic import BaseModel


class AuthRequest(BaseModel):
    init_data: str  # raw initData string from the Telegram Web App SDK


class AuthResponse(BaseModel):
    token: str
    user_id: int
    first_name: str
    is_premium: bool


class SubjectOut(BaseModel):
    id: int
    title: str
    order: int

    class Config:
        from_attributes = True


class ModuleOut(BaseModel):
    id: int
    label: str
    order: int

    class Config:
        from_attributes = True


class MaterialOut(BaseModel):
    id: int
    title: str
    page_count: int | None

    class Config:
        from_attributes = True


class QuestionOut(BaseModel):
    """Note: correct_option is deliberately excluded — never send the answer to the client."""
    id: int
    text: str
    option_a: str
    option_b: str
    option_c: str
    option_d: str

    class Config:
        from_attributes = True


class AnswerRequest(BaseModel):
    question_id: int
    selected_option: str  # 'a' | 'b' | 'c' | 'd'


class AnswerResponse(BaseModel):
    correct: bool
    correct_option: str
    free_questions_remaining: int | None = None  # null if user is premium


class ProgressOut(BaseModel):
    module_id: int
    last_question_index: int
    correct_count: int
    completed: bool

    class Config:
        from_attributes = True
