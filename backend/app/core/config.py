from functools import lru_cache
from pathlib import Path
import os

from dotenv import load_dotenv
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parents[3]
load_dotenv(BASE_DIR / ".env")


class Settings(BaseModel):
    app_name: str = os.getenv("APP_NAME", "InsightHub")
    app_env: str = os.getenv("APP_ENV", "development")
    backend_host: str = os.getenv("BACKEND_HOST", "127.0.0.1")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "8501"))
    sqlite_path: Path = Path(os.getenv("SQLITE_PATH", BASE_DIR / "data" / "insighthub.db"))
    chroma_path: Path = Path(os.getenv("CHROMA_PATH", BASE_DIR / "data" / "chroma"))
    upload_path: Path = Path(os.getenv("UPLOAD_PATH", BASE_DIR / "data" / "uploads"))
    groq_api_key: str = os.getenv("GROQ_API_KEY", "")
    groq_model: str = os.getenv("GROQ_MODEL", "llama-3.1-70b-versatile")
    embedding_model: str = os.getenv("EMBEDDING_MODEL", "BAAI/bge-m3")


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    settings = Settings()
    settings.sqlite_path.parent.mkdir(parents=True, exist_ok=True)
    settings.chroma_path.mkdir(parents=True, exist_ok=True)
    settings.upload_path.mkdir(parents=True, exist_ok=True)
    return settings
