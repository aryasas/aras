from typing import Optional
from sqlalchemy import String, Integer, Boolean, ForeignKey, DateTime, Text
from sqlalchemy.orm import relationship, Mapped, mapped_column, Session
from core import Aras
from core.response import ok
from datetime import datetime, timezone

class WebPage(Aras.Model):
    __tablename__ = "web_page"
    __public__ = True  # public read; writes still plan-gated via write_saas_module
    slug: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    meta_title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    meta_description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_published: Mapped[bool] = mapped_column(Boolean, default=False)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    template: Mapped[str] = mapped_column(String(50), default="default", info={"choices": ["default", "full_width", "landing"]})
    sort_order: Mapped[int] = mapped_column(Integer, default=0)

    @Aras.model_action(name="publish", permission="edit", label="Publish", icon="Check")
    def publish(self, db):
        self.is_published = True
        self.published_at = datetime.now(timezone.utc)
        db.add(self)
        db.flush()
        return ok({}, message="Page published.")

    @Aras.model_action(name="unpublish", permission="edit", label="Unpublish", icon="X")
    def unpublish(self, db):
        self.is_published = False
        self.published_at = None
        db.add(self)
        db.flush()
        return ok({}, message="Page unpublished.")

class WebMenuItem(Aras.Model):
    __tablename__ = "web_menu_item"
    __public__ = True  # public read
    label: Mapped[str] = mapped_column(String(100), nullable=False)
    url: Mapped[str] = mapped_column(String(500), nullable=False)
    parent_id: Mapped[Optional[int]] = mapped_column(ForeignKey("web_menu_item.id"), nullable=True)
    menu_location: Mapped[str] = mapped_column(String(50), info={"choices": ["header", "footer", "both"]})
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

    parent = relationship(lambda: WebMenuItem, remote_side="WebMenuItem.id", backref="children")

class ContactSubmission(Aras.Model):
    __tablename__ = "web_contact_submission"
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    subject: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False)
    replied_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)

    @Aras.model_action(name="mark_read", permission="edit", label="Mark Read", icon="MailOpen")
    def mark_read(self, db):
        self.is_read = True
        return ok({}, message="Marked as read.")

class SiteSetting(Aras.Model):
    __tablename__ = "web_site_setting"
    __public__ = True  # public read
    key: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    group: Mapped[str] = mapped_column(String(50), default="general", info={"choices": ["general", "seo", "social", "contact"]})


# gemini-flash
class LandingSection(Aras.Model):
    __tablename__ = "web_landing_section"
    __public__ = True  # public read
    key: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    subtitle: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    cta_label: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    cta_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
    is_visible: Mapped[bool] = mapped_column(Boolean, default=True)

    # gemini-flash
    @Aras.model_action(name="reorder", permission="edit")
    def reorder(self, db: Session, sort_order: int):
        self.sort_order = sort_order
        db.add(self)
        db.commit()
        db.refresh(self)
        return ok({"id": self.id, "sort_order": self.sort_order}, message=f"Landing section {self.key} reordered.")
