# -*- coding: utf-8 -*-
"""
arasCore/lib/app_helper.py
==========================
AppHelper — standard declaration yang dibuat oleh setiap code-based app
di file manifest.py-nya. Framework membaca ini saat startup untuk:

  1. Mendaftarkan models ke universal API registry (/api/<app>/<resource>/)
  2. Mendaftarkan custom API handlers (override generic CRUD jika perlu)
  3. Menghasilkan /admin/<app>/<resource>/ dan sidebar menu otomatis
  4. Membaca SubHandler per resource untuk override logic CRUD

Konvensi:
  - Setiap app_* menaruh manifest.py di root folder-nya
  - manifest.py berisi satu instance: helper = AppHelper(...)
  - Framework membaca helper ini via blueprints.py

Contoh manifest.py sederhana (SOC):

    helper = AppHelper(
        name="soc", title="Social",
        resources=[ResourceDef("posts", SocPost, serializer=post_serializer)],
        custom_routes=[CustomRoute("/feed", feed_handler)],
    )

Contoh manifest.py dengan sub-modul (ERP):

    helper = AppHelper(
        name="erp", title="ERP",
        menu_groups=[
            MenuGroup("Accounting", "fa-calculator", [
                ResourceDef("acc/account", AccAccount, handler=AccHandler()),
                ResourceDef("acc/journal", AccJournal, handler=JournalHandler()),
            ]),
            MenuGroup("CRM", "fa-handshake-o", [
                ResourceDef("crm/customer", CrmCustomer),
            ]),
        ],
    )
"""
import logging
from dataclasses import dataclass, field
from typing import Callable, Optional, Type

logger = logging.getLogger(__name__)


class SubHandler:
    """
    Custom handler untuk satu resource. App extend class ini dan override
    method yang perlu dikustomisasi. Framework cek apakah ResourceDef punya
    handler — jika ya, pakai method dari sini; jika tidak, pakai generic CRUD.

    Method yang bisa dioverride:
        list(query)      → ubah query sebelum dieksekusi (filter, order, dll)
        before_create(data, obj) → validasi / enrichment sebelum INSERT
        after_create(obj)        → side-effect setelah INSERT (sequence, audit, dll)
        before_update(data, obj) → validasi sebelum UPDATE
        after_update(obj)        → side-effect setelah UPDATE
        before_delete(obj)       → cek apakah boleh dihapus
        serialize(obj)   → custom serializer (override ResourceDef.serializer jika keduanya ada)

    Contoh:

        class JournalHandler(SubHandler):
            def list(self, query):
                return query.filter_by(is_posted=False)

            def before_create(self, data, obj):
                if not data.get("ref"):
                    raise ValueError("ref wajib diisi")

            def after_create(self, obj):
                from aras.app_erp.erp_acc.services import generate_sequence
                obj.number = generate_sequence("JV")
    """

    def list(self, query):
        """Override untuk filter/sort query list. Kembalikan query object."""
        return query

    def before_create(self, data: dict, obj):
        """Dipanggil sebelum db.session.add(obj). Raise Exception untuk cancel."""
        pass

    def after_create(self, obj):
        """Dipanggil setelah commit INSERT."""
        pass

    def before_update(self, data: dict, obj):
        """Dipanggil sebelum commit UPDATE. Raise Exception untuk cancel."""
        pass

    def after_update(self, obj):
        """Dipanggil setelah commit UPDATE."""
        pass

    def before_delete(self, obj):
        """Dipanggil sebelum delete. Raise Exception untuk cancel."""
        pass

    def serialize(self, obj) -> Optional[dict]:
        """Override untuk custom serialization. Return None untuk pakai default."""
        return None


@dataclass
class ResourceDef:
    """
    Deklarasi satu resource (model) yang diekspos ke framework.

    Attributes:
        name:         URL slug, e.g. "acc/journal" → /api/erp/acc/journal/
        model:        SQLAlchemy model class
        serializer:   Optional callable(obj) -> dict. Default: column serializer.
        handler:      Optional SubHandler instance untuk override CRUD logic.
        readonly:     Jika True, hanya GET yang diizinkan.
        require_auth: Butuh login. Default True.
        admin_list:   Tampilkan di sidebar & admin list. Default True.
        list_columns: [(Label, field)] untuk kolom di admin list view.
        menu_title:   Override judul di sidebar. Default: nama di-titlecase.
        menu_icon:    Icon FA untuk item ini di sidebar.
    """
    name: str
    model: Optional[Type] = None
    serializer: Optional[Callable] = None
    handler: Optional[SubHandler] = None
    readonly: bool = False
    require_auth: bool = True
    admin_list: bool = True
    list_columns: list = field(default_factory=list)
    menu_title: Optional[str] = None
    menu_icon: str = "fa-table"
    required_permissions: list = field(default_factory=list)
    url: Optional[str] = None  # custom URL override; skips auto-generated CRUD route
    searchable: list = field(default_factory=list)   # column names searched by ?q=
    filters: list = field(default_factory=list)       # column names usable in ?filter[field]=
    show_save_btn: bool = True  # show Save button in form view; set False for read-only/custom-save resources

    def get_menu_title(self) -> str:
        if self.menu_title:
            return self.menu_title
        slug = self.name.split("/")[-1]
        return slug.replace("-", " ").replace("_", " ").title()

    def get_serializer(self):
        """Cek handler.serialize dulu, lalu ResourceDef.serializer, lalu None."""
        if self.handler:
            result = self.handler.serialize
            if result is not SubHandler.serialize:
                return result
        return self.serializer


@dataclass
class MenuGroup:
    """
    Grup resources di sidebar, untuk app besar seperti ERP.
    Setiap group tampil sebagai sub-section di sidebar dengan icon sendiri.

    Attributes:
        title:     Judul group, e.g. "Accounting"
        icon:      Font Awesome icon, e.g. "fa-calculator"
        resources: List ResourceDef yang masuk ke group ini
        order:     Urutan di dalam app (0 = paling atas)
    """
    title: str
    icon: str
    resources: list = field(default_factory=list)
    order: int = 0


@dataclass
class CustomRoute:
    """
    Custom API route — framework mount ke /api/<app>/<path>/.
    Logic ada di handler function. Dipakai untuk endpoint non-CRUD
    (e.g. feed, search, posting jurnal, dll).

    Attributes:
        path:         Path relatif dari /api/<app>/, e.g. "/feed"
        handler:      Flask view function
        methods:      HTTP methods, default ["GET"]
        require_auth: Default True
    """
    path: str
    handler: Callable
    methods: list = field(default_factory=lambda: ["GET"])
    require_auth: bool = True


class AppHelper:
    """
    Manifest deklarasi untuk satu code-based app.
    Diinstansiasi di manifest.py setiap app, dibaca framework saat startup.

    Args:
        name:          App slug, e.g. "erp", "soc"
        title:         Display name, e.g. "ERP", "Social"
        resources:     List ResourceDef (flat) — untuk app sederhana
        menu_groups:   List MenuGroup — untuk app besar (ERP, dll).
                       Jika diisi, framework pakai ini untuk sidebar;
                       resources flat TIDAK perlu diisi lagi.
        custom_routes: List CustomRoute — endpoint non-CRUD
        admin_icon:    Font Awesome icon class, e.g. "fa-building"
        admin_order:   Urutan app di sidebar (lebih kecil = lebih atas)
    """

    def __init__(
        self,
        name: str,
        title: str,
        resources: list = None,
        menu_groups: list = None,
        custom_routes: list = None,
        admin_icon: str = "fa-cubes",
        admin_order: int = 99,
        home_url: str = None,
        settings_schema: list = None,
        admin_slug: str = None,
        api_slug: str = None,
        template: str = None,
    ):
        self.name = name
        self.title = title
        self.menu_groups = menu_groups or []
        self.custom_routes = custom_routes or []
        self.admin_icon = admin_icon
        self.admin_order = admin_order
        self.settings_schema = settings_schema or []
        self.home_url = home_url
        # admin_slug: overrides /admin/<name>/ URL prefix (e.g. admin_slug="social" → /admin/social/)
        self.admin_slug = admin_slug or name
        # api_slug: overrides /api/<name>/ URL prefix (e.g. api_slug="social" → /api/social/)
        self.api_slug = api_slug or name
        # template: base Jinja2 template for app's public (non-admin) pages
        self.template = template

        # Flat resources: ambil dari menu_groups jika tidak diisi eksplisit
        if resources:
            self.resources = resources
        elif menu_groups:
            self.resources = [r for g in menu_groups for r in g.resources]
        else:
            self.resources = []

    def get_api_prefix(self) -> str:
        return f"/api/{self.api_slug}"

    def get_admin_prefix(self) -> str:
        return f"/admin/{self.admin_slug}"

    def to_menu_dict(self) -> dict:
        """
        Kembalikan dict struktur menu untuk sidebar.
        Jika ada menu_groups, children berisi groups.
        Jika tidak, children berisi resources langsung.
        """
        adm = self.get_admin_prefix()

        if self.menu_groups:
            children = []
            for grp in sorted(self.menu_groups, key=lambda g: g.order):
                grp_children = [
                    {
                        "title": res.get_menu_title(),
                        "icon":  res.menu_icon,
                        "url":   res.url if res.url else f"{adm}/{res.name}/",
                    }
                    for res in grp.resources if res.admin_list
                ]
                if grp_children:
                    # Group URL points to the group home page (tiles view)
                    grp_slug = grp.title.lower().replace(" ", "-")
                    children.append({
                        "title":    grp.title,
                        "icon":     grp.icon,
                        "url":      f"{adm}/{grp_slug}/",
                        "children": grp_children,
                    })
        else:
            children = [
                {
                    "title":    res.get_menu_title(),
                    "icon":     res.menu_icon,
                    "url":      res.url if res.url else f"{adm}/{res.name}/",
                    "children": [],
                }
                for res in self.resources if res.admin_list
            ]

        # Append Settings link as last child (framework auto-mounts this route)
        children.append({
            "title":    "Settings",
            "icon":     "fa-cog",
            "url":      f"{adm}/settings/",
            "children": [],
        })

        # Top-level app link di sidebar: default ke /admin/<app>/ home page
        # (framework auto-mounts a standard home page). `home_url` still wins
        # if explicitly set by the app for a fully custom landing page.
        top_url = self.home_url or f"{adm}/"

        return {
            "title":    self.title,
            "icon":     self.admin_icon,
            "order":    self.admin_order,
            "url":      top_url,
            "children": children,
            "source":   "manifest",
            "app_slug": self.name,
        }

    def __repr__(self):
        return (
            f"<AppHelper name={self.name!r} "
            f"resources={len(self.resources)} "
            f"groups={len(self.menu_groups)} "
            f"custom_routes={len(self.custom_routes)}>"
        )
