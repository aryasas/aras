from typing import Optional
from datetime import date
from sqlalchemy import String, ForeignKey, Date
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..base import MasterDataBase

class Department(MasterDataBase):
    __tablename__ = "erp_hr_departments"
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_hr_departments.id"), nullable=True)

class Position(MasterDataBase):
    __tablename__ = "erp_hr_positions"
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_hr_departments.id"), nullable=True)

class Employee(MasterDataBase):
    __tablename__ = "erp_hr_employees"
    party_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_party_parties.id"), nullable=True)
    department_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_hr_departments.id"), nullable=True)
    position_id: Mapped[Optional[int]] = mapped_column(ForeignKey("erp_hr_positions.id"), nullable=True)
    employee_code: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    join_date: Mapped[Optional[date]] = mapped_column(Date, nullable=True)
    employment_type: Mapped[str] = mapped_column(String(50), default="full_time")
    status: Mapped[str] = mapped_column(String(50), default="active")
