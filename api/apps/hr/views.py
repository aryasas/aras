from core import Aras
from .models import Department, Position, Employee

class DepartmentView(Aras.View):
    model = Department
    title = "Departments"
    icon = "Network"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name"],
        },
    ]

class PositionView(Aras.View):
    model = Position
    title = "Positions"
    icon = "Contact"
    layout = [
        {
            "key": "general",
            "title": "General",
            "fields": ["name"],
        },
    ]

class EmployeeView(Aras.View):
    model = Employee
    title = "Employees"
    icon = "Users"
    layout = [
        {
            "key": "identity",
            "title": "Identity",
            "fields": ["name", "department_id", "position_id", "employment_type", "status"],
        },
        {
            "key": "dates",
            "title": "Dates",
            "fields": ["join_date", "exit_date"],
        },
    ]
