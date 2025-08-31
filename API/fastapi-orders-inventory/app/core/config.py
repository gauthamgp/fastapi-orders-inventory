from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # SQLite for now (simple & file-based). You can swap this later.
    DATABASE_URL: str = "sqlite:///./app.db"
    ECHO_SQL: bool = False  # turn True while debugging SQL

    # Webhook security
    PAYMENT_WEBHOOK_SECRET: str = "change-me-in-.env"   # set in .env for real
    WEBHOOK_MAX_SKEW_SECONDS: int = 300                 # 5 minutes
    
    class Config:
        env_file = ".env"  # optional, for overrides in deployment

settings = Settings()
