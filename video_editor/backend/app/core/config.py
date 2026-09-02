from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "AI Video Creation Platform API"
    app_version: str = "1.0.0"
    environment: str = "development"

    # -----------------------------------
    # Base URL
    # -----------------------------------

    base_url: str = "http://127.0.0.1:8001"

    # -----------------------------------
    # Provider selection
    # -----------------------------------

    image_provider: str = "huggingface"
    video_provider: str = "local"
    tts_provider: str = "edge"

    # -----------------------------------
    # Hugging Face configuration
    # -----------------------------------

    hf_token: str = ""

    # -----------------------------------
    # ElevenLabs configuration
    # -----------------------------------

    elevenlabs_api_key: str = ""
    elevenlabs_tts_model: str = "eleven_multilingual_v2"

    # -----------------------------------
    # Runway configuration
    # -----------------------------------

    runwayml_api_secret: str = ""

    # -----------------------------------
    # LTX configuration
    # -----------------------------------

    ltx_api_key: str = ""

    # -----------------------------------
    # Environment configuration
    # -----------------------------------

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


settings = Settings()