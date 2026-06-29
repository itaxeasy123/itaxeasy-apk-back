from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "itaxeasy-apk-backend"
    ENVIRONMENT: str = "local"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/itaxeasy"

    # JWT (our own session tokens issued AFTER MSG91 verifies the phone OTP)
    JWT_SECRET: str = "supersecretjwtkeyforitaxeasyapkbackend"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 60  # 60 days

    # MSG91 OTP (https://control.msg91.com)
    # The backend proxies OTP send/verify to MSG91's OTP API; MSG91 generates,
    # delivers (DLT SMS) and stores the OTP, so we never hold the code ourselves.
    MSG91_AUTH_KEY: str = ""
    MSG91_TEMPLATE_ID: str = ""
    MSG91_SENDER_ID: str = ""  # optional 6-char DLT header (blank = template default)
    MSG91_OTP_EXPIRY_MINUTES: int = 5
    MSG91_OTP_LENGTH: int = 6
    MSG91_BASE_URL: str = "https://control.msg91.com/api/v5"

    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT == "local"

    # Read .env file if it exists
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
