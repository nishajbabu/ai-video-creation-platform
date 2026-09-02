from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Media Generation API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # Base URL used when generating public media URLs.
    base_url: str = "http://127.0.0.1:8000"

    # -----------------------------------
    # Provider selection
    # -----------------------------------

    image_provider: str = "existing"
    video_provider: str = "local"
    tts_provider: str = "edge"

    # -----------------------------------
    # ElevenLabs configuration
    # -----------------------------------

    elevenlabs_api_key: str = ""
    elevenlabs_tts_model: str = "eleven_multilingual_v2"

    # -----------------------------------
    # Hugging Face configuration
    # -----------------------------------

    hf_token: str = ""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()