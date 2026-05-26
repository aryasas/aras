from core import Aras
from .models import HandoffRun, TemplateAnnotation

class HandoffRunView(Aras.View):
    model = HandoffRun
    title = "Agent Runs"
    icon = "Network"


class TemplateAnnotationView(Aras.View):
    model = TemplateAnnotation
    title = "Template Annotations"
    icon = "Tag"
