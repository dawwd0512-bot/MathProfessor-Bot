import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")

    DEFAULT_PROVIDER = os.getenv("DEFAULT_PROVIDER", "gemini")

    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.6-flash")

    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
    OPENROUTER_MODEL = os.getenv(
        "OPENROUTER_MODEL",
        "openai/gpt-4.1-mini"
    )

    WORKSPACE = "workspace"
    MEMORY = "memory"
    LOGS = "logs"

    @classmethod
    def check(cls):
        errors = []

        if not cls.TELEGRAM_BOT_TOKEN:
            errors.append("TELEGRAM_BOT_TOKEN")

        if cls.DEFAULT_PROVIDER == "gemini" and not cls.GEMINI_API_KEY:
            errors.append("GEMINI_API_KEY")

        if cls.DEFAULT_PROVIDER == "openrouter" and not cls.OPENROUTER_API_KEY:
            errors.append("OPENROUTER_API_KEY")

        return errors
