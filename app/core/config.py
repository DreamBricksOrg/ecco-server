"""Configurações centrais da aplicação"""

from pydantic import Field
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Optional

class Settings(BaseSettings):
    """Configurações da aplicação"""
    
    # Database Configuration
    MONGO_URI: Optional[str] = Field(default=None, env="MONGO_URI")
    MONGO_DB: str = Field("intel", env="MONGO_DB")
    
    # JWT Configuration
    JWT_SECRET: Optional[str] = Field(default=None, env="JWT_SECRET")
    JWT_ALGORITHM: str = Field("HS256", env="JWT_ALGORITHM")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(60 * 24, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    ADMIN_CREATION_TOKEN: Optional[str] = Field(default=None, env="ADMIN_CREATION_TOKEN")
    
    # Monitoring Configuration
    SENTRY_DSN: Optional[str] = Field(default=None, env="SENTRY_DSN")
    LOG_API: Optional[str] = Field(default=None, env="LOG_API")
    LOG_ID: Optional[str] = Field(default=None, env="LOG_ID")
    
    # External Services
    SHORTENER_BASE_URL: Optional[str] = Field(default="https://go.dbpe.com.br", env="SHORTENER_BASE_URL")
    SHORTENER_USER: Optional[str] = Field(default=None, env="SHORTENER_USER")
    SHORTENER_PASSWORD: Optional[str] = Field(default=None, env="SHORTENER_PASSWORD")
    CADASTRO_BASE_URL: Optional[str] = Field(default="https://clarotvboxchute.ngrok.app/api/claro/cta", env="CADASTRO_BASE_URL")
    
    # Communication Configuration
    UDP_PORT: int = Field(5004, env="UDP_PORT")
    SERIAL_PORT: str = Field("COM3", env="SERIAL_PORT")
    SERIAL_BAUDRATE: int = Field(9600, env="SERIAL_BAUDRATE")
    
    # OBS WebSocket Settings
    OBS_HOST: str = Field("localhost", env="OBS_HOST")
    OBS_PORT: int = Field(4455, env="OBS_PORT")
    OBS_PASSWORD: str = Field("v5rk4RQAqy9uX9Eb", env="OBS_PASSWORD")
    OBS_RECORDING_DIR: str = Field(default="./recordings", env="OBS_RECORDING_DIR")
        
    # Server Settings
    HOST: str = Field("0.0.0.0", env="HOST")
    PORT: int = Field(8000, env="PORT")
    RELOAD: bool = Field(True, env="RELOAD")
    
    # Logging Settings
    LOG_LEVEL: str = Field("INFO", env="LOG_LEVEL")
    LOG_FILE: str = Field("app.log", env="LOG_FILE")
    
    # Environment Settings
    ENVIRONMENT: str = Field("development", env="ENVIRONMENT")
    DEBUG: bool = Field(True, env="DEBUG")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        extra = "ignore"

@lru_cache()
def get_settings() -> Settings:
    """Retorna as configurações da aplicação (cached)"""
    return Settings()