from core import Aras
from .models import HandoffRun, TemplateAnnotation, StyleOverride

class HandoffRunView(Aras.View):
    model = HandoffRun
    title = "Agent Runs"
    icon = "Network"


class TemplateAnnotationView(Aras.View):
    model = TemplateAnnotation
    title = "Template Annotations"
    icon = "Tag"


# claude-opus-4-7
class StyleOverrideView(Aras.View):
    model = StyleOverride
    title = "Style Overrides"
    icon = "Paintbrush"
