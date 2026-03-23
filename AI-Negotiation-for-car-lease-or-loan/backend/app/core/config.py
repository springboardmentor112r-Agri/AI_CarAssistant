from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
  DATABASE_URL: str
  GROQ_API_KEY: str = ""
  ANTHROPIC_API_KEY: str = ""
  OPENAI_API_KEY: str = ""
  GOOGLE_CLOUD_CREDENTIALS_JSON: str = "{}"

  # Access token — 15 minutes
  JWT_SECRET: str
  JWT_EXPIRE_MINUTES: int = 15

  # Refresh token — 7 days (separate secret for rotation safety)
  JWT_REFRESH_SECRET: str = ""
  JWT_REFRESH_EXPIRE_DAYS: int = 7

  # Cookie settings
  # Development : COOKIE_SECURE=false, COOKIE_SAMESITE=lax
  # Production  : COOKIE_SECURE=true,  COOKIE_SAMESITE=none
  COOKIE_SECURE: bool = False
  COOKIE_SAMESITE: str = "lax"
  COOKIE_DOMAIN: str = ""

  QDRANT_URL: str = ""
  QDRANT_API_KEY: str = ""
  BREVO_API_KEY: str = ""
  EMAIL_FROM: str = "noreply@example.com"
  FRONTEND_URL: str = "http://localhost:5173"
  CORS_ADDITIONAL_ORIGINS: str = ""
  CORS_ALLOW_ORIGIN_REGEX: str = ""
  APP_BASE_URL: str = "http://localhost:8000"
  ADMIN_EMAIL: str = ""

  # Render sets PORT env var
  PORT: int = 8000

  model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
