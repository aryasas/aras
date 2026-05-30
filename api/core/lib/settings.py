import os
import secrets
import logging
from dotenv import load_dotenv

_current = os.path.dirname(os.path.abspath(__file__))
_api_root = os.path.dirname(os.path.dirname(_current))   # api/
_project_root = os.path.dirname(_api_root)               # aras/

load_dotenv(dotenv_path=os.path.join(_project_root, ".env"), override=True)

_logger = logging.getLogger(__name__)

_MODE = os.getenv("ARAS_MODE", "production").lower()


def _build_db_url(default_name: str) -> str:
    """Build DATABASE_URL from DB_* components, or use DATABASE_URL directly if set."""
    if os.getenv("DATABASE_URL"):
        return os.getenv("DATABASE_URL")  # type: ignore[return-value]
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME") or default_name
    pw = f":{password}" if password else ""
    return f"postgresql+psycopg2://{user}{pw}@{host}:{port}/{name}"


class BaseSettings:
    APP_NAME: str = os.getenv("APP_NAME", "Aras")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "30"))
    PASSWORD_RESET_EXPIRE_MINUTES: int = int(os.getenv("PASSWORD_RESET_EXPIRE_MINUTES", "15"))
    CORS_ORIGINS: list = [
        o.strip() for o in os.getenv("CORS_ORIGINS", "http://localhost:5173").split(",")
        if o.strip()
    ]
    ARAS_ADMIN_PASSWORD: str = os.getenv("ARAS_ADMIN_PASSWORD", "")
    RBAC_ENABLED: bool = os.getenv("RBAC_ENABLED", "true").lower() not in ("false", "0", "no")
    DEBUG: bool = False
    TESTING: bool = False
    DATABASE_URL: str = _build_db_url("aras")

    def validate(self):
        if not self.SECRET_KEY:
            if self.DEBUG or self.TESTING:
                self.SECRET_KEY = secrets.token_hex(32)
                _logger.warning("SECRET_KEY not set — generated ephemeral key. Tokens invalidate on restart.")
            else:
                raise RuntimeError(
                    "SECRET_KEY must be set in production. "
                    "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
                )
        if not self.ARAS_ADMIN_PASSWORD:
            if self.DEBUG or self.TESTING:
                self.ARAS_ADMIN_PASSWORD = "admin"
                _logger.warning("ARAS_ADMIN_PASSWORD not set — using default 'admin'.")
            else:
                raise RuntimeError("ARAS_ADMIN_PASSWORD must be set in production.")


class DevelopmentSettings(BaseSettings):
    DEBUG = True
    RBAC_ENABLED = os.getenv("RBAC_ENABLED", "false").lower() not in ("false", "0", "no")
    DATABASE_URL: str = _build_db_url("dev")


class TestingSettings(BaseSettings):
    DEBUG = True
    TESTING = True
    RBAC_ENABLED = False
    DATABASE_URL: str = _build_db_url("arastest")


class ProductionSettings(BaseSettings):
    DEBUG = False
    DATABASE_URL: str = _build_db_url("aras")


_config_map = {
    "development": DevelopmentSettings,
    "testing": TestingSettings,
    "production": ProductionSettings,
}

Settings = _config_map.get(_MODE, ProductionSettings)
settings = Settings()
