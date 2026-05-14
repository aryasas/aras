import os
import secrets
import logging
from dotenv import load_dotenv

_current = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.dirname(os.path.dirname(_current))
load_dotenv(dotenv_path=os.path.join(_api_root, ".env"))

_logger = logging.getLogger(__name__)


class Settings:
    DATABASE_URL: str = (
        os.getenv("SQLALCHEMY_DATABASE_URI") or
        os.getenv("DATABASE_URL") or
        "mysql+pymysql://root:@localhost/aras"
    )
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))
    CORS_ORIGINS: list = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]
    ARAS_ADMIN_PASSWORD: str = os.getenv("ARAS_ADMIN_PASSWORD", "")
    APP_NAME: str = os.getenv("APP_NAME", "Aras")
    DEBUG: bool = os.getenv("ARAS_MODE", "production").lower() == "development"

    def validate(self):
        if not self.SECRET_KEY:
            if self.DEBUG:
                self.SECRET_KEY = secrets.token_hex(32)
                _logger.warning(
                    "SECRET_KEY not set — generated ephemeral key. Tokens invalidate on restart."
                )
            else:
                raise RuntimeError(
                    "SECRET_KEY must be set in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        if not self.ARAS_ADMIN_PASSWORD:
            if self.DEBUG:
                self.ARAS_ADMIN_PASSWORD = "admin"
                _logger.warning(
                    "ARAS_ADMIN_PASSWORD not set — using default 'admin'. Set it in .env for production."
                )
            else:
                raise RuntimeError("ARAS_ADMIN_PASSWORD must be set in production.")

settings = Settings()
