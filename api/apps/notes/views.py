from core import Aras
from .models import Note

class NoteView(Aras.View):
    model = Note
    title = "Notes"
    icon = "pi pi-pencil"
