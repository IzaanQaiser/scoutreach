from pydantic import AnyHttpUrl, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str | None = None
    llm_provider: str | None = None
    llm_model: str | None = None
    hunter_api_key: SecretStr | None = None
    gmail_client_id: str | None = None
    gmail_client_secret: SecretStr | None = None
    app_base_url: AnyHttpUrl | None = None

    model_config = SettingsConfigDict(env_prefix="", extra="ignore")


settings = Settings()
