from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    OPENAI_API_KEY: str
    PINECONE_API_KEY: str
    REDIS_URL: str
    CLIENT_URL: str
    JWT_SECRET: str

    ADMIN_EMAIL: str
    ADMIN_PASSWORD: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: str
    MAIL_FROM: str
    MAIL_FROM_NAME: str = "Resolution Engine"
    MAIL_SERVER: str
    MAIL_PORT: int = 465
    MAIL_STARTTLS: bool = False
    MAIL_SSL_TLS: bool = True

    class Config:
        env_file = ".env"


settings = Settings()
