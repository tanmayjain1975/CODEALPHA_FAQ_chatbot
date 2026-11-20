"""Application settings, overridable through environment variables."""

import os
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "local-faq-assistant")
    FAQS_PATH = Path(os.getenv("FAQS_PATH", str(BASE_DIR / "faqs.json")))
    SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.30"))
    MAX_QUESTION_LENGTH = 1000
    HOST = os.getenv("HOST", "127.0.0.1")
    PORT = int(os.getenv("PORT", "5000"))
    DEBUG = os.getenv("FLASK_DEBUG", "0").lower() in {"1", "true", "yes"}
