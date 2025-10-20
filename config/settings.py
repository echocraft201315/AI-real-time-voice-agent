from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "Voice Agent"
    DEBUG: bool = False
    GROQ_API_KEY: str
    OPENAI_API_KEY: str
    DEEPGRAM_API_KEY: str
    HF_TOKEN: str
    LANGCHAIN_PROJECT: str
    LANGCHAIN_TRACING_V2: str = "false"
    PYTHONDONTWRITEBYTECODE: int = 1
    REDIS_HOST: str
    REDIS_PORT: int

    def configure_environment(self):
        """Set up environment-specific configurations"""
        import os
        os.environ["HF_TOKEN"] = self.HF_TOKEN
        os.environ["LANGCHAIN_PROJECT"] = self.LANGCHAIN_PROJECT
        os.environ["LANGCHAIN_TRACING_V2"] = self.LANGCHAIN_TRACING_V2

    class Config:
        env_file = ".env"