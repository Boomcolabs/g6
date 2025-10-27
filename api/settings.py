"""API environment configuration file"""
from pydantic_settings import BaseSettings, SettingsConfigDict


class ApiSettings(BaseSettings):
    """
    Model that manages API server settings.

    - Actual environment variable values can be set in the .env file.
    - If the .env file is missing or values are not set, the default values of the ApiSettings class are used.
    """
    # Declare settings for the .env file to read.
    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        extra='ignore',  # extra=forbid (default)
        frozen=True  # Set to make values immutable.
    )

    API_VERSION: str = "v1"

    AUTH_ALGORITHM: str = "HS256"  # JWT algorithm
    AUTH_ISSUER: str = "g6_rest_api"  # JWT issuer
    AUTH_AUDIENCE: str = "g6_rest_api"  # JWT audience

    ACCESS_TOKEN_EXPIRE_MINUTES: float = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: float = 60 * 24 * 14  # 14 days

    # JWT Secret Key
    # For security, environment variables in the .env file must be set.
    ACCESS_TOKEN_SECRET_KEY: str = "access_token_secret_key"
    REFRESH_TOKEN_SECRET_KEY: str = "refresh_token_secret_key"


api_settings = ApiSettings()
