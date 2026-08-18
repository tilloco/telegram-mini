from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Postgres connection string, e.g.
    # postgresql://user:password@host:5432/dbname
    # Leave empty in .env to fall back to local SQLite automatically.
    database_url: str = ""

    # Bot token from @BotFather — used to verify Telegram initData
    telegram_bot_token: str = ""

    # Where uploaded PDF study materials get saved
    media_root: str = "./media/pdfs"

    # How long a session token stays valid, in hours
    session_ttl_hours: int = 24 * 30
   # Gemini API key for AI question-answering — https://aistudio.google.com
    gemini_api_key: str = ""

    class Config:
        env_file = ".env"


settings = Settings()
if not settings.database_url:
    settings.database_url = "sqlite:///./local.db"
