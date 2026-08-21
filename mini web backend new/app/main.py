import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.config import settings
from app.routers import auth, content, quiz, ai 
from fastapi.responses import FileResponse
from app.routers import admin
app.include_router(admin.router)
# Creates tables on startup if they don't exist yet.
# Fine for now — once the schema stabilizes, switch to Alembic migrations.
Base.metadata.create_all(bind=engine)

os.makedirs(settings.media_root, exist_ok=True)

app = FastAPI(title="Law Quiz Mini App API")
@app.get("/index.html")
def serve_frontend():
    frontend_path = os.path.join(os.path.dirname(__file__), "..", "index.html")
    return FileResponse(frontend_path)

# The Mini App frontend runs inside Telegram's webview, on its own origin
# (e.g. your Render static site URL), so CORS must allow it explicitly.
# TODO: once you know your frontend's deployed URL, replace "*" with that
# exact URL for better security.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(content.router)
app.include_router(quiz.router)
app.include_router(ai.router)

@app.get("/")
def health_check():
    return {"status": "ok", "service": "lawquiz-miniapp-backend"}
