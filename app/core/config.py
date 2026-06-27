from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "itaxeasy-apk-backend"
    ENVIRONMENT: str = "local"

    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/itaxeasy"

    # JWT (our own session tokens issued AFTER Firebase verifies the phone OTP)
    JWT_SECRET: str = "supersecretjwtkeyforitaxeasyapkbackend"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7  # 7 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 60  # 60 days

    # Firebase Admin SDK
    # Path to the service-account JSON downloaded from the Firebase console.
    # The backend uses this only to VERIFY the Firebase ID token sent by the app;
    # OTP send/verify happens on-device via the Firebase Phone Auth SDK (free).
    FIREBASE_CREDENTIALS_PATH: str = "firebase-service-account.json"
    # Optional explicit project id (otherwise inferred from the credentials file)
    FIREBASE_PROJECT_ID: str = ""

    @property
    def is_local(self) -> bool:
        return self.ENVIRONMENT == "local"

    # Read .env file if it exists
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
