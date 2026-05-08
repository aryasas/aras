# -*- coding: utf-8 -*-
"""
app/todo/models/task.py
=======================
Showcase model: one class produces table + REST API + admin CRUD + sidebar tile.

Declarative meta keys consumed by the framework:
  __app__   : owning app slug (matches manifest app name)
  __menu__  : sidebar group on the app home page (optional)
  __title__ : human label (optional; default = humanised class name)
  __url__   : URL slug under /api/<app>/ and /admin/<app>/ (optional; default = kebab(class))
  __icon__  : Font-Awesome icon for menu tile

Field types are inferred from name (`due_date` → Date, `is_done` → Boolean,
`description` → Text); declare explicitly to override.
"""

from arasCore.arasgen import ArasGen
class Task(ArasGen.Model):
    __tablename__ = "todo_task"
    __app__       = "todo"
    __menu__      = "Tasks"
    __title__     = "My Tasks"
    __icon__      = "fa-check-square-o"
    # __url__ defaults to "task"

    title       = ArasGen.String(null=False, length=200)
    description = ArasGen.Col()                 # → Text
    due_date    = ArasGen.Col()                 # → Date
    is_done     = ArasGen.Col(default=False)    # → Boolean
