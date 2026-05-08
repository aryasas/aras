# -*- coding: utf-8 -*-
"""
app/todo/manifest.py
====================
Declarative app — symmetric with ArasModel. The Todo class compiles to an
AppHelper instance; the framework picks up `helper` at startup. Models are
imported first so the registry is populated before the metaclass runs.
"""
from arasCore.arasgen import ArasGen
from app.todo import models  # noqa: F401  — import registers ArasModels

class Todo(ArasGen.App):
    name  = "todo"
    title = "Todo"
    icon  = "fa-check-square-o"
    order = 30
    # menu_groups auto-derived from registered models (Task → "Tasks" group)

helper = Todo.helper
