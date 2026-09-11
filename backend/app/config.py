from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "MicroLawyer AI API"
    environment: str = "development"
    frontend_origin: str = "http://localhost:3000"
    supabase_url: str = ""
    supabase_service_role_key: str = ""
    embedding_model: str = "sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2"
    groq_api_key: str = ""
    groq_chat_model: str = "openai/gpt-oss-120b"
    groq_whisper_model: str = "whisper-large-v3-turbo"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
