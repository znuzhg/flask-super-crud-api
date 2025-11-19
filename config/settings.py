import os
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv


load_dotenv()  # load .env if present


@dataclass
class BaseConfig:
    DEBUG: bool = False
    TESTING: bool = False
    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-me")

    # Database
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL",
        "mysql+pymysql://root:password@localhost:3306/test",
    )

    # JWT
    JWT_SECRET: str = os.getenv("JWT_SECRET", "change-me")
    JWT_ALG: str = os.getenv("JWT_ALG", "HS256")
    ACCESS_TOKEN_EXPIRES: int = int(os.getenv("ACCESS_TOKEN_EXPIRES", "600"))
    REFRESH_TOKEN_EXPIRES: int = int(os.getenv("REFRESH_TOKEN_EXPIRES", "2592000"))

    # Logging
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    # HTTP
    MAX_CONTENT_LENGTH: int = int(os.getenv("MAX_CONTENT_LENGTH", str(2 * 1024 * 1024)))  # 2MB
    CORS_ORIGINS: str = os.getenv("CORS_ORIGINS", "*")

    # Redis / Queue
    REDIS_URL: Optional[str] = os.getenv("REDIS_URL")

    # JSON logging toggle
    LOG_JSON: bool = os.getenv("LOG_JSON", "false").lower() == "true"


@dataclass
class DevConfig(BaseConfig):
    DEBUG: bool = True


@dataclass
class TestConfig(BaseConfig):
    TESTING: bool = True
    DEBUG: bool = True
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite+pysqlite:///:memory:")


@dataclass
class ProdConfig(BaseConfig):
    DEBUG: bool = False


def _validate_required(cfg: BaseConfig) -> None:
    missing = []
    if not cfg.SECRET_KEY:
        missing.append("SECRET_KEY")
    if not cfg.JWT_SECRET:
        missing.append("JWT_SECRET")
    if not cfg.DATABASE_URL:
        missing.append("DATABASE_URL")
    if missing and not cfg.TESTING:
        raise RuntimeError(f"Missing required configuration variables: {', '.join(missing)}")


def get_settings() -> BaseConfig:
    env = (os.getenv("APP_ENV") or os.getenv("FLASK_ENV") or os.getenv("ENV") or "dev").lower()
    if env in {"prod", "production"}:
        cfg: BaseConfig = ProdConfig()
    elif env in {"test", "testing"}:
        cfg = TestConfig()
    else:
        cfg = DevConfig()
    _validate_required(cfg)
    return cfg


settings = get_settings()
