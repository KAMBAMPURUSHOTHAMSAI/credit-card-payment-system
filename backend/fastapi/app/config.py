from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DB_NAME: str = "credit_card_payment_system"
    DB_USER: str = "credit_user"
    DB_PASSWORD: str = ""
    DB_HOST: str = "localhost"
    DB_PORT: int = 3306

    JWT_SECRET_KEY: str = "change-me"
    JWT_ALGORITHM: str = "HS256"

    PAYMENT_SUCCESS_RATE: int = 80

    # =====================================================
    # EMAIL NOTIFICATIONS
    # =====================================================

    EMAIL_NOTIFICATIONS_ENABLED: bool = False

    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""

    SMTP_USE_TLS: bool = True
    SMTP_USE_SSL: bool = False

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True,
    )

    @property
    def database_url(self) -> str:
        return (
            f"mysql+pymysql://"
            f"{self.DB_USER}:"
            f"{self.DB_PASSWORD}@"
            f"{self.DB_HOST}:"
            f"{self.DB_PORT}/"
            f"{self.DB_NAME}"
        )


settings = Settings()