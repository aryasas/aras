from typing import Optional
from sqlalchemy import String, Text, Integer, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime
from core import Aras


# unattributed (pre-tagging)
class HandoffRun(Aras.Model):
    __tablename__ = "dev_handoff_runs"
    __searchable_fields__ = ["feature", "mode", "status"]
    __display_fields__ = ("feature",)
    __layout__ = [
        {
            "title": "Overview",
            "fields": ["feature", "mode", "status", "run_date"]
        },
        {
            "title": "Prompt (Claude Spec)",
            "fields": ["prompt_md"]
        },
        {
            "title": "Agent Output",
            "fields": ["backend_files", "frontend_files", "output_md"]
        },
        {
            "title": "Token Usage",
            "fields": [
                "gemini_prompt_tokens", "gemini_completion_tokens",
                "gpt_prompt_tokens", "gpt_completion_tokens",
                "total_tokens", "total_requests"
            ]
        },
        {
            "title": "Issues",
            "fields": ["issues"]
        },
        {
            "title": "Claude Review",
            "fields": ["claude_verdict", "revision_count", "claude_review"]
        },
        {
            "title": "Meta",
            "fields": ["author", "notes"]
        },
    ]

    feature: Mapped[str] = mapped_column(String(300))
    mode: Mapped[str] = mapped_column(String(50))           # full | backend-only | frontend-only
    status: Mapped[str] = mapped_column(String(50))         # success | error | partial
    run_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    prompt_md: Mapped[str] = mapped_column(Text, nullable=True)     # full handoff.md spec Claude wrote

    backend_files: Mapped[str] = mapped_column(Text, nullable=True)   # newline-separated file paths
    frontend_files: Mapped[str] = mapped_column(Text, nullable=True)  # newline-separated file paths
    output_md: Mapped[str] = mapped_column(Text, nullable=True)       # appended status blocks from agents

    gemini_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    gemini_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    gpt_prompt_tokens: Mapped[int] = mapped_column(Integer, default=0)
    gpt_completion_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0)
    total_requests: Mapped[int] = mapped_column(Integer, default=0)

    issues: Mapped[str] = mapped_column(Text, nullable=True)

    # Claude review
    claude_verdict: Mapped[str] = mapped_column(String(20), nullable=True)   # APPROVED | NEEDS-FIX
    claude_review: Mapped[str] = mapped_column(Text, nullable=True)          # full review text
    revision_count: Mapped[int] = mapped_column(Integer, default=0)          # how many revision cycles ran

    # Manual/direct change fields (populated when source != multi_agent)
    author: Mapped[str] = mapped_column(String(100), nullable=True)          # Claude Code | human | gemini | codex
    notes: Mapped[str] = mapped_column(Text, nullable=True)                  # free-form notes for manual runs

    # Git tracking
    commit_hash: Mapped[Optional[str]] = mapped_column(String(40), nullable=True)
    commit_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)


# claude-opus-4-7
class StyleOverride(Aras.Model):
    """
    Universal per-element style overrides applied to live pages by the Template Builder.
    Scope is either 'global' (all routes) or a route prefix like '/notes/' (matches startswith).
    `selector` is a CSS selector resolved by the runtime injector against the live DOM.
    `css_json` stores key/value CSS declarations (e.g. {"color": "#222", "padding": "12px"}).
    """
    __tablename__ = "dev_style_overrides"
    __searchable_fields__ = ["scope", "selector", "label"]
    __display_fields__ = ("scope", "selector")

    scope: Mapped[str] = mapped_column(String(200), index=True, default="global")
    selector: Mapped[str] = mapped_column(String(500), index=True)
    label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    css_json: Mapped[dict] = mapped_column(JSON, default=dict)
    text_override: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    hidden: Mapped[bool] = mapped_column(default=False)


# unattributed (pre-tagging)
class TemplateAnnotation(Aras.Model):
    """
    Persists template layouts and AI annotations for the Template Builder dev tool.
    """
    __tablename__ = "dev_template_annotations"
    __searchable_fields__ = ["template_name", "author", "node_id", "node_kind", "status"]
    __display_fields__ = ("template_name", "node_id", "status")
    __layout__ = [
        {
            "title": "General",
            "fields": ["template_name", "author", "created_at"]
        },
        {
            "title": "Annotation Data",
            "fields": ["node_id", "node_kind", "node_label", "breakpoint", "status", "comment"]
        },
        {
            "title": "Tree Data",
            "fields": ["tree_json", "sections"]
        }
    ]

    template_name: Mapped[str] = mapped_column(String(100), index=True)
    author: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    sections: Mapped[list] = mapped_column(JSON, default=list)

    # New fields for Craft.js editor
    node_id: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    node_kind: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    node_label: Mapped[Optional[str]] = mapped_column(String(200), nullable=True)
    breakpoint: Mapped[Optional[str]] = mapped_column(String(20), nullable=True)
    status: Mapped[str] = mapped_column(String(50), default="pending")
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    tree_json: Mapped[Optional[dict]] = mapped_column(JSON, nullable=True)
