from core import Aras
from .models import Note

class Notes(Aras.App):
    app_name = "notes"
    app_label = "Notes"
    icon = "StickyNote"
    models = [Note]