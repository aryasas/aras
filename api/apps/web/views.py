from core import Aras
from .models import WebPage, WebMenuItem, ContactSubmission, SiteSetting, LandingSection


class WebPageView(Aras.View):
    model = WebPage
    title = "Pages"
    icon = "FileText"


class WebMenuItemView(Aras.View):
    model = WebMenuItem
    title = "Menu Items"
    icon = "Menu"


class ContactSubmissionView(Aras.View):
    model = ContactSubmission
    title = "Contact Submissions"
    icon = "Mail"


class SiteSettingView(Aras.View):
    model = SiteSetting
    title = "Site Settings"
    icon = "Settings"


# gemini-flash
class LandingSectionView(Aras.View):
    model = LandingSection
    title = "Landing Sections"
    icon = "Image"
