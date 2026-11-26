from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application configuration loaded from environment variables and .env."""

    APP_NAME: str = "LMS API"
    APP_ENV: str = "development"
    DEBUG: bool = False
    ENABLE_API_DOCS: bool = False

    DATABASE_URL: str = "mysql+pymysql://root:password@localhost:3306/lms_db"

    JWT_SECRET_KEY: str = "change-this-to-a-strong-random-secret-key"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    RESET_TOKEN_EXPIRE_MINUTES: int = 15

    # Password policy
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPER: bool = True
    PASSWORD_REQUIRE_LOWER: bool = True
    PASSWORD_REQUIRE_DIGIT: bool = True

    FRONTEND_ORIGIN: str = "http://localhost:5173"

    STORAGE_BACKEND: str = "local"
    UPLOAD_DIR: str = "uploads"
    MAX_UPLOAD_SIZE_MB: int = 10

    # Cloudinary (used when STORAGE_BACKEND=cloudinary)
    CLOUDINARY_CLOUD_NAME: str = ""
    CLOUDINARY_API_KEY: str = ""
    CLOUDINARY_API_SECRET: str = ""
    CLOUDINARY_FOLDER: str = "lms_private"

    # Progress & completion policy
    PROGRESS_WEIGHT_LECTURES: float = 0.40
    PROGRESS_WEIGHT_ASSIGNMENTS: float = 0.30
    PROGRESS_WEIGHT_QUIZZES: float = 0.30
    COURSE_COMPLETE_MIN_PROGRESS: float = 80.0
    COURSE_COMPLETE_MIN_ATTENDANCE: float = 75.0
    COURSE_COMPLETE_REQUIRE_ALL_QUIZZES: bool = True

    model_config = SettingsConfigDict(
        env_file=(".env", "backend/.env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",
    )

    @property
    def cors_origins(self) -> list[str]:
        """Return allowed CORS origins parsed from FRONTEND_ORIGIN."""
        return [origin.strip() for origin in self.FRONTEND_ORIGIN.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    """Return cached application settings instance."""
    return Settings()


settings = get_settings()
