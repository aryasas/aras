from core import Aras
from .models import Note
from . import views  # noqa: F401

class Notes(Aras.App):
    app_name = "notes"
    app_label = "Notes"
    icon = "StickyNote"
    models = [Note]