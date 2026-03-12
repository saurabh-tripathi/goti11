from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = "postgresql://goti11_user:password@localhost:5432/goti11_db"
    SECRET_KEY: str = "changeme-set-a-real-secret-key-32-chars-min"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    CRICAPI_KEY: str = ""
    CRICAPI_BASE_URL: str = "https://api.cricapi.com/v1"

    FIRST_ADMIN_USERNAME: str = "admin"
    FIRST_ADMIN_PASSWORD: str = "changeme"
    FIRST_ADMIN_EMAIL: str = "admin@goti11.local"

    SCORE_SYNC_COOLDOWN_SECONDS: int = 120


settings = Settings()
