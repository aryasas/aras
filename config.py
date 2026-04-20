import os
import logging
from dotenv import load_dotenv


load_dotenv()


PROJECT_ROOT_FOLDER = str(os.path.dirname(__file__))
APP_ROOT_FOLDER = str("{}{}".format(PROJECT_ROOT_FOLDER, "/aras"))


class Config:
    PROJECT_ROOT_FOLDER = PROJECT_ROOT_FOLDER
    APP_ROOT_FOLDER = APP_ROOT_FOLDER

    SECRET_KEY = os.getenv("SECRET_KEY") or "hard to guess string"

    STATIC_DIR = PROJECT_ROOT_FOLDER + "/static"
    TEMPLATE_DIR = PROJECT_ROOT_FOLDER + "/templates"

    TEMPLATES_AUTO_RELOAD = True
    EXPLAIN_TEMPLATE_LOADING = False
    RELOADER = True

    CSRF_ENABLED = False
    WTF_CSRF_ENABLED = True

    # SQLALCHEMY
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ADMIN
    ARAS_ADMIN = os.getenv("ARAS_ADMIN")

    # MAIL CONFIG
    MAIL_SUBJECT_PREFIX = "[ARAS]"
    MAIL_SENDER = ["aryasasubiakti@yahoo.com"]
    MAIL_SERVER = "smtp.mail.yahoo.com"
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = os.getenv("MAIL_USERNAME")
    MAIL_PASSWORD = os.getenv("MAIL_PASSWORD")

    # AUTH
    LOGIN_VIEW = "auth.login_view"

    # PAGINATION
    USE_PAGINATION = False
    DEFAULT_PAGINATION_PER_PAGE = 10
    POSTS_PER_PAGE = 5
    FOLLOWER_PER_PAGE = 20
    FOLLOWERS_PER_PAGE = 20

    # DEBUG TOOLBAR
    DEBUG_TB_ENABLED = False  # Disable Debug toolbar
    DEBUG_TB_INTERCEPT_REDIRECTS = False

    # CACHE
    CACHE_TYPE = "SimpleCache"  # Can be "memcached", "redis", etc.

    # CELERY
    CELERY_BROKER_URL = "redis://localhost:6379/10"
    CELERY_RESULT_BACKEND = "redis://localhost:6379/11"

    # SENTRY_USER_ATTRS = ['email']
    # SENTRY_DSN = 'https://ff753a8882b345a393602fea06908097:a08554b86412433aba13f753467947d8@sentry.io/190847'
    # SENTRY_LOGGING = True

    LOGGING_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOGGING_FORMAT = "default"
    LOGGING_LOCATION = "logging.log"
    LOGGING_LEVEL = logging.WARNING
    LOGGING_FILE = PROJECT_ROOT_FOLDER + "/log/logging.log"
    LOGGING_CONFIG = PROJECT_ROOT_FOLDER + "/log/logging.cfg"
    LOGGING_FOLDER = PROJECT_ROOT_FOLDER + "/log/"

    # UPLOAD FOLDER
    UPLOAD_FOLDER = APP_ROOT_FOLDER + "/static/media/"
    UPLOAD_AUDIO_FOLDER = APP_ROOT_FOLDER + "/static/media/audio/"
    UPLOAD_IMAGE_FOLDER = APP_ROOT_FOLDER + "/static/media/img/"
    UPLOAD_DOC_FOLDER = APP_ROOT_FOLDER + "/static/media/doc/"
    UPLOAD_PDF_FOLDER = APP_ROOT_FOLDER + "/static/media/pdf/"
    UPLOAD_TXT_FOLDER = APP_ROOT_FOLDER + "/static/media/txt/"

    IMAGE_ALLOWED_EXTENSIONS = ["png", "jpg", "jpeg", "gif"]
    DOC_ALLOWED_EXTENSIONS = ["txt", "pdf"]

    JSON_SORT_KEYS = False

    # RBAC — set RBAC_ENABLED=false in env to disable all permission checks (dev mode)
    RBAC_ENABLED = os.getenv("RBAC_ENABLED", "true").lower() not in ("false", "0", "no")

    # Enable this if want to load data as dict.
    # This will enable for all data that loaded trough derived view class
    # ModuleRegistry or function module registry in admin/registry.py
    # Please note this may affect performance.
    # set to False if want tnormal DB load.
    LOAD_DATA_AS_DICT = False


class DevelopmentConfig(Config):
    DEBUG = True
    RBAC_ENABLED = False
    DEBUG_TB_ENABLED = True
    DEBUG_TB_PROFILER_ENABLED = False
    DEBUG_TB_TEMPLATE_EDITOR_ENABLED = False
    ASSETS_DEBUG = False  # Don't bundle/minify static assets
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    USE_DEBUGER = (False,)
    USE_RELOADER = (False,)
    PASSTHROUGH_ERROR = False
    CELERY_ALWAYS_EAGER = False
    JSON_AS_ASCII = False
    LOGGING_LEVEL = logging.WARNING


class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = os.getenv("ARAS_DATABASE_URI_TEST")


class ProductionConfig(Config):
    SQLALCHEMY_DATABASE_URI = os.getenv("ARAS_DATABASE_URI_DEV")


config = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
    "default": DevelopmentConfig,
}
