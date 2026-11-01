"""
Central configuration.

Every setting comes from environment variables (or a .env file), so no secret is
ever hardcoded. Read the values anywhere with:  from app.config import settings
"""
import logging
import secrets
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

BACKEND_DIR = Path(__file__).resolve().parent.parent
log = logging.getLogger("careerpilot.config")

GEMINI_OPENAI_BASE = "https://generativelanguage.googleapis.com/v1beta/openai/"


class Settings(BaseSettings):
    # .env is read from the project root or from backend/ (later files win)
    model_config = SettingsConfigDict(env_file=(str(BACKEND_DIR.parent / ".env"), str(BACKEND_DIR / ".env")), extra="ignore")

    # "development" or "production". Production turns on secure cookies and refuses a default secret.
    environment: str = "development"

    # Database: SQLite works with zero setup; use PostgreSQL in production, e.g.
    # postgresql+psycopg://careerpilot:careerpilot@localhost:5432/careerpilot
    # (Render/Railway give "postgres://..." URLs; we convert them automatically.)
    database_url: str = f"sqlite:///{BACKEND_DIR / 'careerpilot.db'}"

    # Auth. SECRET_KEY must be a long random string in production.
    secret_key: str = ""
    jwt_expire_minutes: int = 60 * 24 * 7
    cookie_name: str = "cp_session"
    cookie_secure: bool | None = None  # None = secure in production, not in development
    cookie_samesite: str = "lax"

    # Resume uploads
    upload_dir: str = str(BACKEND_DIR / "uploads")
    max_upload_mb: int = 5

    # ---- AI provider -------------------------------------------------------------
    # LLM_PROVIDER = gemini | openai_compatible | none
    #   gemini: Google Gemini through its OpenAI-compatible endpoint, key = GEMINI_API_KEY
    #   openai_compatible: any OpenAI-style API (OpenAI, IBM watsonx/Granite gateway, Groq,
    #                      Ollama ...), set LLM_BASE_URL + LLM_API_KEY + LLM_MODEL
    #   none: no AI; every feature runs its rule-based engine and says so in the UI
    # Leave LLM_PROVIDER empty to pick automatically from whichever key is set.
    llm_provider: str = ""
    gemini_api_key: str = ""
    gemini_model: str = "gemini-flash-latest"
    llm_base_url: str = ""
    llm_api_key: str = ""
    llm_model: str = ""
    llm_timeout_seconds: float = 45
    llm_max_retries: int = 2

    # Optional: raises GitHub's public API rate limit. Never required.
    github_token: str = ""
    github_enabled: bool = True

    # Comma separated list of frontend origins allowed to call the API from another origin
    # (only needed when the frontend is NOT served by this backend, e.g. `npm run dev`).
    cors_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    # Rate limits (requests per window per client IP)
    rate_limit_auth: str = "10/minute"
    rate_limit_ai: str = "20/minute"
    rate_limit_code: str = "30/minute"

    # Code runner (Python practice tests)
    code_timeout_seconds: float = 4.0
    code_memory_mb: int = 256

    # If this folder exists (the exported Next.js app), FastAPI serves it at "/"
    frontend_dir: str = str(BACKEND_DIR.parent / "frontend" / "out")

    # ---- derived values ---------------------------------------------------------
    @property
    def is_production(self) -> bool:
        return self.environment.lower().startswith("prod")

    @property
    def db_url(self) -> str:
        url = self.database_url
        if url.startswith("postgres://"):
            url = "postgresql+psycopg://" + url[len("postgres://"):]
        elif url.startswith("postgresql://"):
            url = "postgresql+psycopg://" + url[len("postgresql://"):]
        return url

    @property
    def secure_cookies(self) -> bool:
        return self.is_production if self.cookie_secure is None else self.cookie_secure

    @property
    def provider(self) -> str:
        p = self.llm_provider.strip().lower().replace("-", "_")
        if p in ("gemini", "openai_compatible", "none"):
            return p
        if p == "openai":
            return "openai_compatible"
        if self.gemini_api_key.strip():
            return "gemini"
        if self.llm_api_key.strip():
            return "openai_compatible"
        return "none"

    @property
    def llm_ready(self) -> bool:
        """True when an AI provider is configured with a key."""
        p = self.provider
        if p == "gemini":
            return bool(self.gemini_api_key.strip())
        if p == "openai_compatible":
            return bool(self.llm_api_key.strip() and self.llm_base_url.strip() and self.llm_model.strip())
        return False

    def llm_endpoint(self) -> tuple[str, str, str]:
        """(base_url, api_key, model) for the configured provider."""
        if self.provider == "gemini":
            return GEMINI_OPENAI_BASE, self.gemini_api_key.strip(), self.gemini_model.strip() or "gemini-flash-latest"
        return self.llm_base_url.strip(), self.llm_api_key.strip(), self.llm_model.strip()


_DEV_SECRET = secrets.token_urlsafe(48)


@lru_cache
def get_settings() -> Settings:
    s = Settings()
    if not s.secret_key:
        if s.is_production:
            raise RuntimeError("SECRET_KEY must be set in production (a long random string).")
        log.warning("SECRET_KEY not set: using a random key for this run (logins reset on restart).")
        s.secret_key = _DEV_SECRET
    return s


settings = get_settings()
