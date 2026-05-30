# gemini-flash
import datetime
import re
import logging
from sqlalchemy.orm import Session
from sqlalchemy import select
from ..registry.numbering_sequence import NumberingSequence
from .config import config

logger = logging.getLogger(__name__)

class NumberingService:
    _defaults = {}

    @classmethod
    def next(cls, db: Session, doc_type: str, org_id: int = 0) -> str:
        """
        Generates the next sequential number for a document type.
        Atomic via SELECT ... FOR UPDATE.
        """
        now = datetime.datetime.now()
        year = now.year
        
        # 1. Get format from config
        format_key = f"core_config.numbering.{doc_type}"
        fmt = config.get(db, format_key)
        if not fmt:
            fmt = cls._get_default_format(doc_type) or "{prefix}{year}-{seq:04d}"
        
        # 2. Atomic increment
        stmt = select(NumberingSequence).filter_by(
            doc_type=doc_type, 
            org_id=org_id, 
            year=year
        ).with_for_update()
        
        row = db.execute(stmt).scalar_one_or_none()
        if not row:
            row = NumberingSequence(doc_type=doc_type, org_id=org_id, year=year, last_seq=1)
            db.add(row)
            seq = 1
        else:
            row.last_seq += 1
            seq = row.last_seq
        
        return cls._format(fmt, doc_type, seq, now)

    @classmethod
    def peek(cls, db: Session, doc_type: str, org_id: int = 0) -> str:
        """Returns the next formatted number without incrementing."""
        now = datetime.datetime.now()
        year = now.year
        format_key = f"core_config.numbering.{doc_type}"
        fmt = config.get(db, format_key)
        if not fmt:
            fmt = cls._get_default_format(doc_type) or "{prefix}{year}-{seq:04d}"
        
        stmt = select(NumberingSequence).filter_by(doc_type=doc_type, org_id=org_id, year=year)
        row = db.execute(stmt).scalar_one_or_none()
        seq = row.last_seq + 1 if row else 1
        
        return cls._format(fmt, doc_type, seq, now)

    @classmethod
    def _format(cls, fmt: str, doc_type: str, seq: int, now: datetime.datetime) -> str:
        year = now.year
        result = fmt
        result = result.replace("{YYYY}", str(year))
        result = result.replace("{YY}", str(year)[2:])
        result = result.replace("{MM}", f"{now.month:02d}")
        result = result.replace("{DD}", f"{now.day:02d}")
        result = result.replace("{year}", str(year))
        
        def replace_seq(match):
            length = int(match.group(1)) if match.group(1) else 1
            return str(seq).zfill(length)
        
        result = re.sub(r"\{seq:(\d+)\}", replace_seq, result)
        result = result.replace("{seq}", str(seq))
        
        prefix = doc_type.upper()[:3]
        result = result.replace("{prefix}", prefix)
        
        return result

    @classmethod
    def register_doc_type(cls, doc_type: str, default_format: str):
        cls._defaults[doc_type] = default_format

    @classmethod
    def _get_default_format(cls, doc_type: str) -> str:
        return cls._defaults.get(doc_type)

numbering = NumberingService
