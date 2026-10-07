from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    service_name: str = "api-gateway"
    port: int = 3000
    cors_allowed_origins: str = ""
    auth_service_url: str = ""
    user_service_url: str = ""
    post_service_url: str = ""
    category_service_url: str = ""
    message_service_url: str = ""
    notification_service_url: str = ""
    review_service_url: str = ""
    search_service_url: str = ""
    favorite_service_url: str = ""
    connect_timeout: float = 5
    read_timeout: float = 30

    @property
    def cors_origins(self):
        return [origin.strip() for origin in self.cors_allowed_origins.split(",") if origin.strip()]
