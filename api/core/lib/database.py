from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from dotenv import load_dotenv

# Load .env from project root (two levels up from core/lib/)
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

# Gunakan MariaDB/MySQL (Standard untuk ERP)
# Format: mysql+pymysql://user:password@host:port/dbname
DATABASE_URL = os.getenv("SQLALCHEMY_DATABASE_URI", "mysql+pymysql://root:999999@localhost/aras")

# Konfigurasi engine untuk stabilitas di MariaDB
engine = create_engine(
    DATABASE_URL,
    pool_recycle=3600,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
