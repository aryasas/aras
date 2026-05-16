from ..base.view import View
from .app_model import AppModel
from .resource_model import ResourceModel
from .field_model import FieldModel
from .link_model import LinkModel
from .role import Role
from .permission import Permission
from .user_role import UserRole
from .activity_log import ActivityLog
from ..auth.models import User
from .series import Series
from .sys_settings import ArasSetting
from .translation_model import TranslationModel
from .widget_model import WidgetModel
from .dashboard_layout_model import DashboardLayoutModel

class UserView(View):
    model = User
    title = "System Users"

class AppView(View):
    model = AppModel
    title = "Applications"

class ResourceView(View):
    model = ResourceModel
    title = "Resources"

class FieldView(View):
    model = FieldModel
    title = "Fields"

class LinkView(View):
    model = LinkModel
    title = "Links"

class RoleView(View):
    model = Role
    title = "User Roles"

class PermissionView(View):
    model = Permission
    title = "Data Permissions"

class UserRoleView(View):
    model = UserRole
    title = "User-Role Mapping"

class ActivityLogView(View):
    model = ActivityLog
    title = "Audit Trail"

class SeriesView(View):
    model = Series
    title = "Series"

class ArasSettingView(View):
    model = ArasSetting
    title = "System Settings"

class TranslationView(View):
    model = TranslationModel
    title = "UI Translations"

class WidgetView(View):
    model = WidgetModel
    title = "Dashboard Widget"

class DashboardLayoutView(View):
    model = DashboardLayoutModel
    title = "User Dashboard Layout"
