"""
Purpose: DB models for the user-configurable workflow engine.
Context: Loaded by Config app; used by WorkflowManager for DB-driven state transitions.
Impact: Enables users to define states, transitions, and side-effect handlers via GUI.
"""
from typing import Optional
from sqlalchemy import String, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from core import Aras


class WorkflowTemplate(Aras.Model):
    __tablename__ = "erp_config_workflow_templates"
    __features__ = ["audit"]

    name: Mapped[str] = mapped_column(String(200))
    document_type: Mapped[str] = mapped_column(String(100), index=True)  # model.__tablename__
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    states: Mapped[list["WorkflowState"]] = relationship(
        "WorkflowState", back_populates="template", cascade="all, delete-orphan"
    )
    transitions: Mapped[list["WorkflowTransition"]] = relationship(
        "WorkflowTransition", back_populates="template", cascade="all, delete-orphan"
    )


class WorkflowState(Aras.Model):
    __tablename__ = "erp_config_workflow_states"
    __features__ = ["audit"]

    template_id: Mapped[int] = mapped_column(ForeignKey("erp_config_workflow_templates.id"), index=True)
    name: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))
    is_initial: Mapped[bool] = mapped_column(Boolean, default=False)
    is_final: Mapped[bool] = mapped_column(Boolean, default=False)
    sequence: Mapped[int] = mapped_column(Integer, default=10, info={"hidden": True})

    template: Mapped["WorkflowTemplate"] = relationship("WorkflowTemplate", back_populates="states")


class WorkflowTransition(Aras.Model):
    __tablename__ = "erp_config_workflow_transitions"
    __features__ = ["audit"]

    template_id: Mapped[int] = mapped_column(ForeignKey("erp_config_workflow_templates.id"), index=True)
    from_state_id: Mapped[int] = mapped_column(ForeignKey("erp_config_workflow_states.id"))
    to_state_id: Mapped[int] = mapped_column(ForeignKey("erp_config_workflow_states.id"))
    name: Mapped[str] = mapped_column(String(50))
    label: Mapped[str] = mapped_column(String(100))
    icon: Mapped[str] = mapped_column(String(50), default="ArrowRight")
    permission: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sequence: Mapped[int] = mapped_column(Integer, default=10, info={"hidden": True})

    template: Mapped["WorkflowTemplate"] = relationship("WorkflowTemplate", back_populates="transitions")
    from_state: Mapped["WorkflowState"] = relationship("WorkflowState", foreign_keys=[from_state_id])
    to_state: Mapped["WorkflowState"] = relationship("WorkflowState", foreign_keys=[to_state_id])
    actions: Mapped[list["WorkflowAction"]] = relationship(
        "WorkflowAction", back_populates="transition", cascade="all, delete-orphan"
    )


class WorkflowAction(Aras.Model):
    __tablename__ = "erp_config_workflow_actions"
    __features__ = ["audit"]

    transition_id: Mapped[int] = mapped_column(ForeignKey("erp_config_workflow_transitions.id"), index=True)
    handler_name: Mapped[str] = mapped_column(String(100))
    params: Mapped[dict] = mapped_column(JSON, default=dict)
    sequence: Mapped[int] = mapped_column(Integer, default=10, info={"hidden": True})

    transition: Mapped["WorkflowTransition"] = relationship("WorkflowTransition", back_populates="actions")
