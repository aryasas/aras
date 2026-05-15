from .database import SessionLocal
from sqlalchemy import text as _text

class DbWrapper:
    def __call__(self):
        return SessionLocal()
    
    @property
    def text(self):
        return _text

db = DbWrapper()
