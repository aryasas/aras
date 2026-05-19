from core import Aras
from .models import WebPage, WebMenuItem, ContactSubmission, SiteSetting


class WebPageView(Aras.View):
    model = WebPage
    title = "Pages"
    icon = "pi pi-file"


class WebMenuItemView(Aras.View):
    model = WebMenuItem
    title = "Menu Items"
    icon = "pi pi-bars"


class ContactSubmissionView(Aras.View):
    model = ContactSubmission
    title = "Contact Submissions"
    icon = "pi pi-envelope"


class SiteSettingView(Aras.View):
    model = SiteSetting
    title = "Site Settings"
    icon = "pi pi-cog"
