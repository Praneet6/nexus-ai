from functools import lru_cache
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # === Core Infrastructure ===
    database_url: str = "postgresql+asyncpg://nexus:nexuspass@localhost:5432/nexus"
    redis_url: str = "redis://localhost:6379/0"

    # === Auth ===
    jwt_secret: str = "nexus-super-secret-change-in-prod"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 1440  # 24 hours

    # === AI ===
    groq_api_key: str = ""
    model_name: str = "llama-3.3-70b-versatile"

    # === F05 Collective Memory ===
    pinecone_api_key: str = ""
    pinecone_index: str = "nexus-collective"

    # === F06 Trust Engine ===
    trust_debit_escalation: int = 20
    trust_debit_unresolved: int = 10
    trust_debit_long_wait: int = 5
    trust_starting_balance: int = 100

    # === App ===
    app_name: str = "Nexus AI"
    debug: bool = False
    cors_origins: list[str] = ["http://localhost:5173", "http://localhost:80", "http://localhost"]

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
