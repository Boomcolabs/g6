"""Manages .env environment configuration values."""
from pydantic_settings import BaseSettings, SettingsConfigDict
from lib.print_log import PrintLog


ENV_PATH = ".env"


class Settings(BaseSettings):
    """.env file configuration model"""
    # Read .env file and set environment variables.
    model_config = SettingsConfigDict(
        env_file=ENV_PATH,
        env_file_encoding='utf-8',
        extra='ignore',  # extra=forbid (default)
    )

    ADMIN_THEME: str = "basic"  # Admin theme
    APP_IS_DEBUG: bool = False  # Debug mode

    COOKIE_DOMAIN: str = ""  # Cookie domain

    # Database settings
    DB_TABLE_PREFIX: str = "g6_"
    DB_ENGINE: str = ""
    DB_USER: str = ""
    DB_PASSWORD: str = ""
    DB_HOST: str = ""
    DB_PORT: int = 3306
    DB_NAME: str = ""
    DB_CHARSET: str = "utf8mb4"

    IS_RESPONSIVE: bool = True  # Use responsive design

    SESSION_COOKIE_NAME: str = "session"  # Session cookie name
    SESSION_SECRET_KEY: str = ""  # Session secret key

    # SMTP settings
    SMTP_SERVER: str = "localhost"
    SMTP_PORT: int = 25
    SMTP_USERNAME: str = ""
    SMTP_PASSWORD: str = ""

    TIME_ZONE: str = "Asia/Seoul"  # Time zone

    # Editor upload settings
    UPLOAD_IMAGE_RESIZE: bool = False  # Use editor image resize
    UPLOAD_IMAGE_SIZE_LIMIT: int = 20  # Image upload size limit (MB)
    UPLOAD_IMAGE_RESIZE_WIDTH: int = 1200  # Image resize width (px)
    UPLOAD_IMAGE_RESIZE_HEIGHT: int = 2800  # Image resize height (px)
    UPLOAD_IMAGE_QUALITY: int = 80  # Image quality (0~100)

    USE_API: bool = True  # Use API
    USE_TEMPLATE: bool = True  # Use template

    # CORS settings
    CORS_ALLOW_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = False
    CORS_ALLOW_METHODS: str = "*"
    CORS_ALLOW_HEADERS:str = "*"

settings = Settings()


class CORSConfig:
    """CORS configuration"""

    def parse_comma_separated_list(self, value):
        """Convert comma-separated string to list."""
        if value == "*":
            return ["*"]
        return [item.strip() for item in value.split(",") if item.strip()]

    @property
    def allow_origins(self):
        """CORS allowed origins"""
        return self.parse_comma_separated_list(settings.CORS_ALLOW_ORIGINS)

    @property
    def allow_credentials(self):
        """CORS allow credentials"""
        allow_credentials = settings.CORS_ALLOW_CREDENTIALS
        if not isinstance(allow_credentials, bool):
            allow_credentials = settings.CORS_ALLOW_CREDENTIALS.lower() == "true"
        if allow_credentials and self.allow_origins == ["*"]:
            PrintLog.warn("Cannot set allow_origins to allow all and allow_credentials to True together.")
            PrintLog.warn("Setting allow_credentials to False for security.")
            allow_credentials = False
        return allow_credentials

    @property
    def allow_methods(self):
        """CORS allowed methods"""
        return self.parse_comma_separated_list(settings.CORS_ALLOW_METHODS)

    @property
    def allow_headers(self):
        """CORS allowed headers"""
        return self.parse_comma_separated_list(settings.CORS_ALLOW_HEADERS)


cors_config = CORSConfig()